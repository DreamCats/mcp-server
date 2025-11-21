# 轻量 CDP 客户端方案（pychrome + websocket-client）

目的：避免 Playwright 40MB 级依赖，仅用轻量 CDP 客户端连接本地浏览器调试端口，完成扫码登录并抓取 header/cookie。功能等价，但需要更多手写代码和兜底。

## 对比 Playwright 的取舍
- 体积：从 ~40MB 降到 KB 级（`pychrome` + `websocket-client`）。
- 抽象：没有 Page/Context/Wait 封装，需手写 CDP 调用与事件处理，例如 `Network.enable`、`Page.navigate`、`Network.responseReceived`、`Network.getCookies`。
- 可靠性：异常/超时/URL 轮询都要自己实现，Chrome 协议字段变化需自行适配。

## 前置
- 浏览器仍需以调试端口启动（如 `--remote-debugging-port=9222`）。
- Python 依赖最少：`pip install pychrome websocket-client`.

## 最小示例（同步流程示意）
```python
import fnmatch
import time
import pychrome

LOGIN_URL = "https://your-sso-login-url"
CDP = "http://127.0.0.1:9222"
WAIT_URL = "**/home"  # 可选，匹配登录后 URL
TIMEOUT = 180

def main():
    browser = pychrome.Browser(url=CDP)
    tab = browser.new_tab()  # 使用现有标签可 browser.list_tab()[0]

    captured_auth = []
    captured_set_cookie = []
    responses = []

    def on_response(**kwargs):
        resp = kwargs.get("response", {})
        headers = {k.lower(): v for k, v in resp.get("headers", {}).items()}
        if "authorization" in headers:
            captured_auth.append(headers["authorization"])
        if "set-cookie" in headers:
            captured_set_cookie.append(headers["set-cookie"])
        if headers:
            responses.append(
                {
                    "url": resp.get("url"),
                    "status": resp.get("status"),
                    "headers": {
                        k: headers[k]
                        for k in ("authorization", "set-cookie")
                        if k in headers
                    },
                }
            )

    tab.Network.responseReceived = on_response

    tab.start()
    tab.Network.enable()
    tab.Page.enable()
    tab.Page.navigate(url=LOGIN_URL)

    print("请在浏览器中扫码/完成登录...")

    final_url = None
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        tab.wait(1)  # 处理事件队列
        try:
            nav = tab.Page.getNavigationHistory()
            entries = nav.get("entries", [])
            if entries:
                final_url = entries[nav.get("currentIndex", 0)]["url"]
                if WAIT_URL and fnmatch.fnmatch(final_url, WAIT_URL):
                    break
        except Exception:
            pass
    else:
        print("等待登录超时")

    cookies = []
    try:
        cookies = tab.Network.getCookies().get("cookies", [])
    except Exception:
        pass

    tab.stop()

    payload = {
        "login_url": LOGIN_URL,
        "final_url": final_url,
        "headers": {"authorization": list(dict.fromkeys(captured_auth)),
                    "set-cookie": list(dict.fromkeys(captured_set_cookie))},
        "cookies": cookies,
        "responses": responses,
    }
    print(payload)

if __name__ == "__main__":
    main()
```

## 使用步骤
1) 用系统浏览器开启调试端口（同 Playwright 方案）。  
2) 安装依赖：`pip install pychrome websocket-client`.  
3) 运行上方示例或将其嵌入现有 CLI，传入 SSO 登录页。  
4) 在浏览器扫码登录，脚本监听 `Network.responseReceived` 并在结束时调用 `Network.getCookies`，打印/写文件。

## 将现有 CLI 改为轻量实现的思路
- 保留参数界面与输出格式，内部替换为 pychrome 逻辑。  
- 用 `browser.list_tab()`/`new_tab()` 替代 Playwright 的 context/page；用 `Page.navigate` 代替 `page.goto`。  
- 登录完成检测：轮询 `Page.getNavigationHistory` 的当前 URL 与 glob/regex 匹配，或等待用户按 Enter。  
- 捕获逻辑：监听 `Network.responseReceived`，手动提取关心的 header；调用 `Network.getCookies` 获取 cookies。  
- 异常与超时：显式 `while time < deadline: tab.wait(1)`，超时后给出可配置提示。
