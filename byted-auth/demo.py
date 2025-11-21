import requests

# url  = "https://cloud.bytedance.net/auth/api/v1/login"

# url = "https://sso.bytedance.com/cas/login"

# url = "https://cloud.bytedance.net/auth/api/v1/login?bd_sso_3b6da9=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjQzMTEwMTksImlhdCI6MTc2MzcwNjIxOSwiaXNzIjoic3NvLmJ5dGVkYW5jZS5jb20iLCJzdWIiOiJnNjEzN29raGJ4Y2wzcHdsNzlweiIsInRlbmFudF9pZCI6ImhncTN0Y2NwM2kxc2pqbjU4emlrIn0.gnRXqSmTqNsxXXBfIacqXnsVI7bfLSdOx0O0mxW68M-I6C9brVNRGv6Amjblv-Eu9OilUcSDe2lu_u-JGW1gn2bNI0tU_yrW84SuGMI6qYdODvElTI0GBKbbMI18S7VkQVY4sNwODW7QDnCueZTl7DBOZGlibNRL7haA1SpNV8RS3DE8E3prqoUSzAHv6OFsrcXExWok6HRhWYyzwKVL1scHYtJdvkux7cPsabywdjc0DHLsyEAkQ2L9xcwtZj2DSRgcWwPlmxBW4Z77A3Kp4Wz_4gglkCjisLW0rjyk0ZV1ujv2IMp4Z_QttQqN6PV7boPOTfK_HMryQI1_kXnvvg&ticket=ST-1763706219-H1zLUSQfyPguM0fIpGAGLztWxVTZ5em1"

url= "https://cloud.bytedance.net/auth/api/v1/jwt"

url = "https://cloud-ttp-us.bytedance.net/auth/api/v1/jwt"

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
    "Cookie": "CAS_SESSION=1879f7e5d448418d6c514a04f0d37a36"
}

response = requests.get(url, headers=headers)
# response.encoding = "utf-8"
# print(response.text)
print(response.status_code)
print(response.headers)