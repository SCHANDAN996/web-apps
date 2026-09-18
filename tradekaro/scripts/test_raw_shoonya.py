import requests
import json
import base64
import hashlib
import os
import pyotp
from dotenv import load_dotenv

load_dotenv('config/credentials.env')
user_id    = os.getenv('USER_ID')
password   = os.getenv('PASSWORD')
app_key    = os.getenv('API_KEY')
imei       = os.getenv('IMEI')
totp_secret = os.getenv('TOTP_SECRET')
vc         = os.getenv('VC') or user_id 

pwd = hashlib.sha256(password.encode('utf-8')).hexdigest()
app_key = hashlib.sha256(f"{user_id}|{app_key}".encode('utf-8')).hexdigest()

payload = {
    "pwd": pwd,
    "uid": user_id,
    "factor2": pyotp.TOTP(totp_secret).now(),
    "vc": vc,
    "appkey": app_key,
    "imei": imei,
    "source": "API"
}
url = "https://api.shoonya.com/NorenWClientTP/QuickAuth"
print(f"Request URL: {url}")
res = requests.post(url, data={'jData': json.dumps(payload)})
print(f"Status Code: {res.status_code}")
print(f"Response text: {res.text}")
print(f"Headers: {res.headers}")
