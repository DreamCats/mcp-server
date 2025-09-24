import requests

url_token = "https://cloud-ttp-us.bytedance.net/auth/api/v1/jwt"
headers_token = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Cookie": "CAS_SESSION=1865f510d37eb4cf2447d210cbf17686"
            }

response_token = requests.get(url_token, headers=headers_token)
print(response_token.headers["X-Jwt-Token"])

url = "https://logservice-tx.tiktok-us.org/streamlog/platform/microservice/v1/query/trace"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
    "X-Jwt-Token": f"{response_token.headers['X-Jwt-Token']}"
}

body = {"logid":"20250923034643559E874098ED5808B03C","vregion":"US-TTP,US-TTP2","scan_span_in_min":10,"psm_list":["oec.live.promotion_core"]}


response = requests.post(url, headers=headers, json=body)
print(response.text)