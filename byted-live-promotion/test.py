# jwt http url

jwt_url = "https://cloud.bytedance.net/auth/api/v1/jwt"

cookie_value = "1865b3e75cb97b643ce61ca29d1085a6"

cookie_key = "CAS_SESSION"


import requests
import json


jwt_header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
    "Accept":"application/json, text/plain, */*",
    "Accept-Encoding":"gzip, deflate, br, zstd",
    "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8",
    "Cookie": f"{cookie_key}={cookie_value}"
}
jwt_response = requests.get(jwt_url, headers=jwt_header)
# print(jwt_response.status_code)
# print(jwt_response.headers)


psm_url = "https://ms-neptune.tiktok-us.org/api/neptune/ms/service/search"
psm_header = {
    "x-jwt-token":jwt_response.headers["X-Jwt-Token"],
}
psm_params = {
    "keyword":"oec.affiliate.monitor",
    "search_type":"all"
}
psm_response = requests.get(psm_url, headers=psm_header, params=psm_params)
# print(psm_response.status_code)
print(json.dumps(psm_response.json()))