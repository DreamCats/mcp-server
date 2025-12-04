import requests

auth_url = "https://open.larkoffice.com/open-apis/auth/v3/tenant_access_token/internal"

app_id = "cli_a8d667668b73900b"
app_secret = "FS9N0KX5IFrAnu38ANGQegJpyWeOvEr7"

response = requests.post(auth_url, json={
    "app_id": app_id,
    "app_secret": app_secret
})
    
print(response.json())