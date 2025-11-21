# CLI SSO 捕获方案（系统浏览器 + Playwright/CDP）

目标：提供一个命令行工具，拉起本地浏览器让用户扫码登录公司 SSO，并在终端获取登录后的凭证（cookie/headers/token），无需额外下载 Playwright 自带浏览器。

## 方案总览
- 浏览器端：用户用本机 Chrome/Edge，启动时打开远程调试端口（默认 9222）。
- CLI 端：Python 脚本用 Playwright 的 CDP 连接功能 `chromium.connect_over_cdp` 复用已启动的浏览器。
- 登录流程：CLI 打开 SSO 登录页 → 用户扫码/完成登录 → CLI 监听页面/接口响应，抓关键凭证（`Set-Cookie`、`Authorization` 或页面 cookie）。
- 输出与存储：CLI 将凭证打印或写入本地配置文件（如 `~/.byted-auth/config.json`），供后续 API 调用。

## 启动系统浏览器开启调试端口
- macOS Chrome: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222`
- macOS Edge: `"/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" --remote-debugging-port=9222`
- Windows Chrome: `"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222`
- Linux Chrome: `google-chrome --remote-debugging-port=9222`
- 端口占用可改为其他（如 9223），CLI 里的 CDP 地址需同步修改；保持浏览器运行期间端口有效。

## 关键技术点
- Playwright 仅用 CDP 连接，不下载内置浏览器；依赖：`pip install playwright`.
- 使用 `chromium.connect_over_cdp("http://127.0.0.1:9222")` 连接已有浏览器会话。
- 会话获取：
  - 优先复用已有 context（复用用户登录态）；若无则 `browser.new_context()`。
  - 通过 `page.on("response")` 监听登录相关接口，抓 `Set-Cookie` / `Authorization`。
  - 或在登录完成后读取 `context.cookies()`，提取目标域名的 cookie。
- 登录完成判定：
  - 监听 URL 变化（如 SSO 跳转到业务首页 `**/home`）。
  - 或等待特定接口返回 200（如 `/auth/api/v1/userinfo`）。
- 安全：
  - 仅监听本机 `127.0.0.1`，不要暴露调试端口到公网。
  - 输出前提示用户敏感信息用途；默认写入用户家目录配置文件，设置权限 600。

## 仓库内实现
- `cli.py`: 入口 CLI，连接 CDP 打开 SSO 登录页，抓取凭证并输出/存盘。
- `browser.py`: 连接本地浏览器的 CDP，会话与页面生命周期管理。
- `capture.py`: 监听响应、归并 `authorization`/`set-cookie` 等头信息，并提取 cookies。
- `storage.py`: 将抓到的凭证写入 `~/.byted-auth/config.json`（默认 600 权限）。

## 安装与前置
1) Python 3.10+。  
2) 安装库：`pip install playwright`（只装 Python 包，不下载浏览器）。  
3) 先关闭已有 Chrome，再用上文命令开启带 `--remote-debugging-port` 的浏览器。

## 使用手册（推荐流程）
1) 启动浏览器并开放调试端口（示例 9222）：  
   `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222`
2) 运行 CLI（区域可选）：  
   `python cli.py --wait-url "**/home"`  
   - `--cdp-endpoint`: 默认 `http://127.0.0.1:9222`，若端口不同需调整。  
   - `--wait-url`: 登录成功后跳转地址的匹配 glob，如 `**/home`，用于自动判定登录完成。若不填，登录后在终端按 Enter 继续。  
   - `--region`: 选择默认登录页（`cn`/`us`/`i18n`），默认 `cn`。  
     - cn: `https://cloud.bytedance.net/auth/api/v1/login`  
     - us: `https://cloud-ttp-us.bytedance.net/auth/api/v1/login`  
     - i18n: `https://cloud-i18n.bytedance.net/auth/api/v1/login`  
   - `--login-url`: 如需自定义登录页再指定，否则按 region 使用默认。  
   - `--timeout`: 等待 `--wait-url` 的秒数，默认 180。  
   - `--output`: 输出文件路径，默认 `~/.byted-auth/config-<region>.json`。  
   - `--no-write`: 仅打印结果，不写文件。  
   - `--verbose`: 打印捕获的响应摘要，便于调试。
3) 在弹出的浏览器中扫码/完成 SSO，CLI 会捕获 `authorization`/`set-cookie`/cookies 并写入输出文件。  
4) 结果文件内容示意：
   ```json
   {
     "login_url": "https://your-sso-login-url",
     "final_url": "https://product/home",
     "headers": {
       "authorization": ["Bearer ..."],
       "set-cookie": ["ssid=...; Path=/; HttpOnly; Secure"]
     },
     "cookies": [
       {"name": "ssid", "value": "...", "domain": ".example.com", "path": "/", "expires": 1234567890}
     ],
     "responses": [
       {"url": "https://.../auth", "status": 200, "headers": {"authorization": "Bearer ..."}}
    ]
   }
   ```

## 一键启动脚本（run_login.sh）
- 作用：自动找到浏览器并以 CDP 端口启动、激活 `.venv`，然后调用 `cli.py`。默认登录页与 CLI 保持一致。脚本会使用独立的 `./.chrome-profile`，结束时会关闭它启动的浏览器进程。
- 默认命令：  
  `./run_login.sh --wait-url "**/home"`  
  如无可执行权限：`chmod +x run_login.sh`
- 可选环境变量：  
  - `PORT`：CDP 端口，默认 9222。  
  - `REGION`：`cn`/`us`/`i18n` 选择默认登录页。  
  - `LOGIN_URL`：自定义登录页（若设置则覆盖 REGION 默认）。  
  - `WAIT_URL`：登录完成后匹配的 URL glob，留空则登录后回终端按 Enter。  
  - `BROWSER_BIN`：浏览器可执行路径（如需自定义）；未设置时自动探测 Chrome/Edge。  
  - `START_BROWSER`：设为 `0` 可不启动浏览器，前提是你已手动开启 CDP 端口。  
  - `PYTHON`：Python 可执行，默认 `python`。  
- 其他 CLI 参数可直接跟在脚本后（例如 `--verbose`、`--no-write` 等）。

## 适配建议
- 如果 SSO 登录成功后没有固定跳转页，可省略 `--wait-url`，登录完回到终端按 Enter。
- 需要额外 header（如 `x-tt-token`）时，可扩展 `capture.py` 里的 `interesting_headers`。
- 若想避免写文件，配合 `--no-write` 并用管道给后续命令处理。

## 后续增强
- 增加对 Windows 用户的自动路径探测，自动拼启动命令。
- 允许 `--headful-keep` 选项，登录后保持浏览器不关，便于排查。
- 在终端对敏感输出加遮挡，提供 `--quiet` 仅写文件。
- 增加 token 过期检测与刷新逻辑（如检测 `expires_at` 或响应码 401 自动重登）。
