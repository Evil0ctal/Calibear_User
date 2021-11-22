# -*- coding: utf-8 -*-
# @Author  : Evil0ctal
# @Time    : 2021/11/20
# @Function:
# After obtaining the parameters entered by the guests at the front desk, verify it, and submit a POST request to the Senet server to complete the account registration, reset the password, and print the result to the console without an API key.
# 获取前台客人输入的参数后进行校验，无误后向Senet服务器提交POST请求完成注册账户，重置密码，无需API key。


from pywebio import config, session
from pywebio.input import *
from pywebio.output import *
from pywebio.platform.flask import webio_view
from flask import Flask
import requests
import json
import time
import re


app = Flask(__name__)
title = "Calibear Cyber Cafe"
description = "Calibear Cyber Cafe Registration/Reset password。"
headers = {
    "Content-Type": "application/json; charset=UTF-8",
    "Referer": "https://calibear.booking.enes.tech/",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36",
}


def check_email(user_email):
    # 正则检查用户输入是否为Email格式
    regex = re.compile(r"[^@]+@[^@]+\.[^@]+")
    if not regex.match(user_email):
        return "Invalid Email"
    else:
        return None


def error_msg():
    # 输出一个毫无用处的信息
    put_html("<hr>")
    put_error("There was an error happened. Please try again!\nIf multiple attempts still fail, please click Feedback.")
    put_html("<hr>")


def error_log(e):
    # 将错误记录在logs.txt中
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open('logs.txt', 'a') as f:
        f.write(date + ": " + str(e) + '\n')


def registration(user_email):
    # 提交注册POST请求
    try:
        url = "https://calibear.bebooking.enes.tech/user/"
        payload = {"login": user_email}
        response = requests.post(url, data=json.dumps(payload), headers=headers).text
        result = json.loads(response)
        print("注册请求response:\n" + response)
        # 请求失败参考(用户已存在)
        # Response: {"login":["User with such email already exists"],"code":-2}
        if result['login'] != user_email:
            put_error("User with such email already exists!\nPlease try another email or reset your password!")
            put_link('Back to home page', '/')
            return False
        else:
            # 请求成功参考（用户未注册）
            # Response: {"id":3148,"login":"example@example.com"}
            user_id = str(result['id'])
            clear()
            put_success("The Email you input is:\n" + result['login'])
            put_info("An activation code had been sent to your Email.\nPlease input the activation code below to finish registration!")
            return user_id
    except Exception as e:
        error_log(e)
        error_msg()


def activation(activation_code, user_id):
    # 提交激活POST请求
    try:
        payload = {"activation_code": str(activation_code)}
        url = "https://calibear.bebooking.enes.tech/user/" + user_id + "/activate/"
        response = requests.post(url, data=json.dumps(payload), headers=headers).text
        print(response)
        if '1216' in response:
            # 请求失败参考（验证码错误）
            # Response: {"detail":"Invalid user validation code","code":1216}
            clear()
            put_error("Invalid user validation code!\nplease enter the correct code!")
            return False
        else:
            # 请求成功参考（验证码正确）
            # Response: {"token":"eyJ022iOiJKs1QiL123sGciOiJIUzI1NiJ9"}
            return True
    except Exception as e:
        error_log(e)
        error_msg()


def reset_password(user_email):
    # 提交重置密码POST请求
    try:
        url = "https://calibear.bebooking.enes.tech/user/send_reset_password_code/"
        payload = {"login": user_email}
        response = requests.post(url, data=json.dumps(payload), headers=headers).text
        print("重置密码请求response:\n" + response)
        if 'login' in response:
            # 请求失败参考（用户不存在）
            # Response: {"login":["User with such login does not exist"],"code":-2}
            put_error('User with such login does not exist!')
            put_link('Back to home page', '/')
            return False
        else:
            # 请求成功参考（用户存在）
            # Response: null
            clear()
            put_success("You will receive a confirmation code on your Email.")
            put_info("If you did not receive the email, please check your spam.\nAfter successful confirmation, you will receive new password via Email.")
            return True
    except Exception as e:
        error_log(e)
        error_msg()
        put_error('Reason:\n' + str(e))


def reset_password_confirm(user_email, confirmation_code):
    # 提交重置密码验证码POST请求
    try:
        payload = {"login": user_email, "code": confirmation_code}
        url = "https://calibear.bebooking.enes.tech/user/reset_password/"
        response = requests.post(url, data=json.dumps(payload), headers=headers).text
        print("重置密码验证码请求response:\n" + response)
        if "token" in response:
            # 请求成功参考（验证码正确）
            # 成功: {"token":"eyJ022iOiJKs1QiL123sGciOiJIUzI1NiJ9"}
            return 'success'
        else:
            # 请求失败参考
            # 验证码不正确: {"detail":"Invalid user reset password code","code":1910}
            # 验证码次数上限: {"detail":"Exceeded the limit of attempts to enter reset password code","code":1911}
            if "1910" in response:
                clear()
                put_error('Invalid user reset password code!')
                return False
            else:
                clear()
                put_error('Exceeded the limit of attempts to enter reset password code!')
                put_link('Back to home page', '/')
                return 'limit'
    except Exception as e:
        error_log(e)
        error_msg()
        put_error('Reason:\n' + str(e))


def check_balance():
    info = input_group('Please enter username and password', [
        input('username', type=TEXT, name='username', required=True),
        input('password', type=PASSWORD, name='password', required=True)
    ])
    try:
        payload = {"login": info['username'], "password": info['password']}
        url = "https://calibear.bebooking.enes.tech/login/"
        response = requests.post(url, data=json.dumps(payload), headers=headers).text
        json_response = json.loads(response)
        token = json_response['token']
        new_headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Referer": "https://calibear.booking.enes.tech/",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36",
            "authorization": 'token ' + token
        }
        result_url = "https://calibear.bebooking.enes.tech/current_user/"
        r = requests.get(result_url, headers=new_headers).text
        # {"id":3919,"first_name":null,"last_name":null,"amount":"0.00","login":"xlszgskzxicg@metalunits.com"}
        account_info = json.loads(r)
        user_name = account_info['login']
        user_balance = account_info['amount']
        print("检查余额response:\n" + r)
        show_balance_result(user_name, user_balance)
    except Exception as e:
        error_log(e)
        error_msg()
        put_error('Reason:\n' + str(e))


def show_balance_result(user_name, user_balance):
    put_success("Your account balance is below!")
    put_table([
        ['Type', 'Content'],
        ['Username', user_name],
        ['Balance', user_balance]])
    put_link('Back to home page', '/')


def about_popup_window():
    with popup('More Information'):
        put_html('<h3>🏷About</h3>')
        put_markdown('This website is made by [Evil0ctal](https://mycyberpunk.com/)')
        put_markdown('View on GitHub: [Calibear_User](https://github.com/Evil0ctal/Calibear_User/)')
        put_markdown('Official Website: [Calibear Cyber Cafe](https://calibearcybercafe.com/)')
        put_html('<hr>')
        put_html('<h3>💖Make Friends</h3>')
        put_markdown('WeChat：[Evil0ctal](https://github.com/Evil0ctal)')
        put_markdown('Gaming: [Steam](https://steamcommunity.com/id/Evil0ctal)')
        put_markdown('Photography: [Instagram](https://www.instagram.com/evil0ctal/)')
        put_html('<hr>')
        put_markdown('Copyright © 2021 [Calibear LLC.](https://calibearcybercafe.com/)')
        put_markdown('All rights reserved.')


@config(title=title, description=description)
def main():
    # 设置favicon
    favicon_url = "https://raw.githubusercontent.com/Evil0ctal/Calibear_User/main/favicon_io/android-chrome-512x512.png"
    session.run_js("""
        $('#favicon32,#favicon16').remove(); 
        $('head').append('<link rel="icon" type="image/png" href="%s">')
        """ % favicon_url)
    # 修改footer
    session.run_js("""$('footer').remove()""")
    put_markdown("""<div align='center' ><font size='10'>🐻Calibear User Management</font></div>""")
    put_html('<hr>')
    put_row([put_link("Home", '/'),
             put_link("Booking", 'https://calibear.booking.enes.tech', new_window=True),
             put_link("WebStore", 'https://calibearcybercafe.applova.menu/', new_window=True),
             put_button("About", onclick=lambda: about_popup_window(), link_style=True, small=True),
             put_markdown("![Views](https://views.whatilearened.today/views/github/evil0ctal/Calibear_User.svg)")
             ])
    # 核心代码 估值两亿 :)
    email_placeholder = 'example@example.com'
    code_placeholder = 'Number only eg.123456'
    # 要求用户输入选择
    select_options = select('Please select an options to continue', required=True, options=['Registration (New user)', 'Reset password (Forgotten password)', 'Check your balance'])
    if select_options == 'Registration (New user)':
        # 开始时间
        start = time.time()
        user_email = input('Input your email', type=TEXT, validate=check_email, placeholder=email_placeholder)
        if user_email:
            user_id = registration(user_email)
            if user_id:
                activation_status = False
                while not activation_status:
                    activation_code = input('Input your activation code', type=NUMBER, placeholder=code_placeholder)
                    if activation(activation_code, user_id):
                        activation_status = True
                        clear()
                        end = time.time()
                        put_success('Registration Complete!')
                        put_info('An email with the initial password has been sent to your email.\nIf you don’t see it, please try to refresh your email or check your spam.')
                        put_text('Total Time: %.4fs' % (end - start))
                        put_link('Back to home page', '/')
    elif select_options == 'Reset password (Forgotten password)':
        # 开始时间
        start = time.time()
        user_email = input('Input your email', type=TEXT, validate=check_email, placeholder=email_placeholder)
        if user_email:
            if reset_password(user_email):
                confirmation_status = False
                while not confirmation_status:
                    confirmation_code = input('Input your confirmation code', type=NUMBER, placeholder=code_placeholder)
                    if confirmation_code:
                        result = reset_password_confirm(user_email, confirmation_code)
                        if result == 'success':
                            confirmation_status = True
                            clear()
                            end = time.time()
                            put_success("Password Reset Complete!")
                            put_info("A new password had been sent to your email. \nIf you don’t see it, please try to refresh your email or check your spam.")
                            put_text('Total Time: %.4fs' % (end - start))
                            put_link('Back to home page', '/')
                        elif result == 'limit':
                            confirmation_status = True
                            clear()
                            end = time.time()
                            put_error('Exceeded the limit of attempts to enter confirmation code!')
                            put_text('Total Time: %.4fs' % (end - start))
                            put_link('Back to home page', '/')
    elif select_options == 'Check your balance':
        check_balance()


if __name__ == '__main__':
    app.add_url_rule('/', 'webio_view', webio_view(main), methods=['GET', 'POST', 'OPTIONS'])
    app.run(host='0.0.0.0', port=80)
