from flask import Flask, render_template, request
import json as js
from faker import Faker
import requests
import time
app = Flask(__name__)

fake = Faker("zh_CN")

tenant_id = ''
client_id = ''
client_secret = ''
skuId = '314c4481-f395-4525-be8b-2ec4bb1e9d91'
# skuId = '94763226-9b3c-4e75-a931-5c89701abe66'
domain = '@hk2.in'
t_app_id = ""
# 腾讯云验证码 APPID 不需要不设置
t_app_secret = ""
#腾讯云验证码 App Secret Key 不需要不设置


def check_ticket(ticket, ip):
    rand_str = fake.password(length=5, special_chars=False, digits=True, upper_case=True, lower_case=True)
    url = "https://captcha.tencentcloudapi.com/?Action=DescribeCaptchaResult&CaptchaType=9&Version=2019-07-22&Ticket=" + \
           ticket + "&UserIp=" + ip + "&Randstr=" + rand_str + "&CaptchaAppId=" + t_app_id + "&AppSecretKey=" + \
           t_app_secret + "&NeedGetCaptchaTime=1&Timestamp=" + str(int(time.time()))
    print(url)
    x = requests.get(url)
    print(x.text)



def get_ms_token():
    url = 'https://login.microsoftonline.com/' + tenant_id + '/oauth2/v2.0/token'
    scope = 'https://graph.microsoft.com/.default'
    post_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': scope
    }
    header = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    x = requests.post(url, data=post_data, headers=header)
    json = js.loads(x.text)
    results = json["access_token"]
    return results


def assign_license(email, token):
    url = 'https://graph.microsoft.com/v1.0/users/' + email + '/assignLicense'
    post_data = {
        "addLicenses": [{
            "disabledPlans": [],
            "skuId": skuId
        }],
        "removeLicenses": []
    }
    header = {
        'Authorization': 'Bearer ' + token,
    }
    x = requests.post(url, json=post_data, headers=header)

    results = js.loads(x.text)

    if "error" not in results:
        return True
    else:
        return False


def create_o365user(first_name, last_name, user_name, token):
    url = 'https://graph.microsoft.com/v1.0/users'
    password = fake.password(length=10, special_chars=True, digits=True, upper_case=True, lower_case=True)
    print(password)
    post_data = {
        "accountEnabled": True,
        "displayName": first_name + ' ' + last_name,
        "mailNickname": user_name,
        "passwordPolicies": "DisablePasswordExpiration, DisableStrongPassword",
        "passwordProfile": {
            "password": password,
            "forceChangePasswordNextSignIn": True
        },
        "userPrincipalName": user_name + domain,
        "usageLocation": "CN"
    }
    header = {
        'Authorization': 'Bearer ' + token,
    }
    x = requests.post(url, json=post_data, headers=header)
    results = js.loads(x.text)

    if "error" in results:
        if results["error"]["message"] == 'Another object with the same value for property userPrincipalName already exists.':
            return {"stat": 'username exists'}
        return results
    assign_results = assign_license(user_name + domain, token)

    if assign_results:
        account = {
            "stat": 'success',
            "email": user_name + domain,
            "password": password
        }
        return account
    else:
        account = {
            "stat": assign_results
        }
        return account


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/createUser', methods=["POST"])
def create_user():
    json = js.loads(request.stream.read())
    first_name = json['firstname']
    last_name = json['lastname']
    user_name = json['username']
    ip = request.remote_addr
    #ticket = json['t_ticket']
    ms_token = get_ms_token()
    #check_ticket(ticket, ip)
    account = create_o365user(first_name, last_name, user_name, ms_token)
    return js.dumps(account)


if __name__ == '__main__':
    app.run()
