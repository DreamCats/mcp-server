import requests

url = "https://bits.bytedance.net/api/v1/dev/task/changes?devBasicId=1862036"

headers = {
    "x-jwt-token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJwYWFzLnBhc3Nwb3J0LmF1dGgiLCJleHAiOjE3NjQ2Nzg2NDgsImlhdCI6MTc2NDY3NDk4OCwidXNlcm5hbWUiOiJtYWlmZW5nIiwidHlwZSI6InBlcnNvbl9hY2NvdW50IiwicmVnaW9uIjoiY24iLCJ0cnVzdGVkIjp0cnVlLCJ1dWlkIjoiZWQ5NmIyY2UtNTRiNi00YjA2LThjNDEtNjI1YmViMDFiODk3Iiwic2l0ZSI6Im9ubGluZSIsImJ5dGVjbG91ZF90ZW5hbnRfaWQiOiJieXRlZGFuY2UiLCJieXRlY2xvdWRfdGVuYW50X2lkX29yZyI6ImJ5dGVkYW5jZSIsInNjb3BlIjoiYnl0ZWRhbmNlIiwic2VxdWVuY2UiOiJSRCIsIm9yZ2FuaXphdGlvbiI6IuS6p-WTgeeglOWPkeWSjOW3peeoi-aetuaehC1HbG9iYWwgRS1Db21tZXJjZS3nvo7lm70t5YaF5a6555S15ZWGLeWGheWuuSIsIndvcmtfY291bnRyeSI6IkNITiIsImxvY2F0aW9uIjoiQ04iLCJhdmF0YXJfdXJsIjoiaHR0cHM6Ly9zMS1pbWZpbGUuZmVpc2h1Y2RuLmNvbS9zdGF0aWMtcmVzb3VyY2UvdjEvdjJfNDk4ZDI1MmItOGM3ZC00NDBjLWI4YzgtZTdmNjJhOTMwMTRnfj9pbWFnZV9zaXplPW5vb3BcdTAwMjZjdXRfdHlwZT1cdTAwMjZxdWFsaXR5PVx1MDAyNmZvcm1hdD1wbmdcdTAwMjZzdGlja2VyX2Zvcm1hdD0ud2VicCIsImVtYWlsIjoibWFpZmVuZ0BieXRlZGFuY2UuY29tIiwiZW1wbG95ZWVfaWQiOjUwMTM2MjYsIm5ld19lbXBsb3llZV9pZCI6NTAxMzYyNn0.Y7pagJK4sEIji3T_D1rVxpFSc6oV5unR1eJx30279mDwQNBGxT9G7UMmel9ObqFvQrL6rvYTefmfIG4K6V2zf3gD_4qzS1mi1HMIp-x51rDpWuGqkhcsCqXKzvcjcQlwgeVsry9iKuTQaLD2LNTTqXY15eI0GClfJNRm17bmA10",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    # "Accept-Encoding": "gzip, deflate, br, zstd"
}

resp = requests.get(url, headers=headers)
print(resp.json())
