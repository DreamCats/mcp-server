# 浏览器扩展方案：区域按钮 + CAS_SESSION 提取

需求目标：点击扩展图标，弹出区域选择按钮（cn/us/i18n），一键读取对应域下的 `CAS_SESSION` cookie 并显示/复制，不依赖 DevTools 或本地服务。

## 功能流程
- Popup 内提供三个按钮：cn / us / i18n，对应不同域名与登录页。
- 用户点击某个区域按钮后：
  1) 根据区域映射选择要查询的域名与登录 URL（默认：  
     - cn: 域 `.bytedance.net`，登录 `https://cloud.bytedance.net/auth/api/v1/login`  
     - us: 域 `.bytedance.net`（可兼容 `.bytedance.com`），登录 `https://cloud-ttp-us.bytedance.net/auth/api/v1/login`  
     - i18n: 域 `.bytedance.net`，登录 `https://cloud-i18n.bytedance.net/auth/api/v1/login`）  
  2) 用 `chrome.cookies.getAll({ domain })` 读取 cookies（含 HttpOnly）。  
  3) 过滤并提取 `CAS_SESSION` 的 value，展示在 UI，支持「复制」按钮。若未找到则提示空状态。  
  4) 可选：列出当前 tab URL 及选定域名，便于确认来源。
- 允许手动切换域名（输入框或下拉）以适配其他环境；记住上次选择。

## Manifest（MV3）
- 权限：`cookies`, `activeTab`.
- host_permissions：按区域域名声明（示例：`https://*.bytedance.net/*`, `https://*.bytedance.com/*`），避免 `<all_urls>`。
- action：`default_popup` 指向 `popup.html`；`default_icon` 提供 16/32/128 图标。
- background：`service_worker`（`background.js`）；如需 clipboard fallback，可用 `offscreen` 文档。

## 文件结构
- `manifest.json`
- `background.js`：封装 `getCookiesByDomain(domain)`，响应来自 popup 的消息。
- `popup.html` / `popup.js`：渲染区域按钮、结果显示、复制功能。
- `offscreen.html` / `offscreen.js`（可选）：在 clipboard 被限制时使用。
- `icons/`：扩展图标。

## 核心逻辑示例
```js
// popup.js
const DOMAIN_MAP = {
  cn: ".bytedance.net",
  us: ".bytedance.net", // 若业务在 .bytedance.com，可按需改为 .bytedance.com
  i18n: ".bytedance.net",
};
const LOGIN_URL_MAP = {
  cn: "https://cloud.bytedance.net/auth/api/v1/login",
  us: "https://cloud-ttp-us.bytedance.net/auth/api/v1/login",
  i18n: "https://cloud-i18n.bytedance.net/auth/api/v1/login",
};

async function fetchCas(region) {
  const res = await chrome.runtime.sendMessage({
    type: "GET_CAS",
    domain: DOMAIN_MAP[region],
  });
  if (!res.ok) throw new Error(res.error);
  return res.casValue; // string | null
}

["cn","us","i18n"].forEach((r) => {
  document.getElementById(`btn-${r}`).onclick = async () => {
    try {
      const cas = await fetchCas(r);
      document.getElementById("region").textContent = r;
      document.getElementById("value").textContent = cas || "(未找到 CAS_SESSION)";
      document.getElementById("login-url").textContent = LOGIN_URL_MAP[r];
    } catch (e) {
      document.getElementById("value").textContent = `错误: ${e.message}`;
    }
  };
});
```

```js
// background.js
async function getCasSession(domain) {
  const cookies = await chrome.cookies.getAll({ domain });
  const cas = cookies.find((c) => c.name === "CAS_SESSION");
  return cas ? cas.value : null;
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "GET_CAS") {
    getCasSession(msg.domain)
      .then((value) => sendResponse({ ok: true, casValue: value }))
      .catch((err) => sendResponse({ ok: false, error: err.message }));
    return true; // async
  }
});
```

## 交互与体验
- Popup 默认显示当前 tab URL 与可点击的区域按钮；点击后立即显示 `CAS_SESSION`。  
- 「复制」按钮将当前展示值写入剪贴板；失败时给出提示并建议检查权限。  
- 若需要调整域名，提供小型输入框或下拉并存储在 `chrome.storage.local`。  
- 错误提示覆盖：无活动 tab、无权限、未找到 cookie、调用异常。

## 安全与合规
- 仅声明必要域名；不要采集其他 cookie。  
- UI 提示 `CAS_SESSION` 为敏感信息，复制前进行提示。  
- 不向外部网络发送数据；仅在本地展示/复制。需发送时，限制为 `127.0.0.1` 并显式告知用户。
