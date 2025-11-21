// Background service worker for ByteDance SSO Auth Capture extension

/**
 * Extract CAS_SESSION cookie value using an exact URL first, then falling back to domain scan.
 * Prefers the cookie that matches the provided URL host/path to avoid picking an older value
 * from another subdomain.
 * @param {Object} options
 * @param {string} [options.url] - Full URL of the active tab (preferred)
 * @param {string} [options.domain] - Fallback domain for broad queries
 * @returns {Promise<string|null>} CAS_SESSION value or null if not found
 */
async function getCasSession({ url, domain }) {
  const targetUrl = url;
  const fallbackDomain = domain;

  try {
    // First, try an exact lookup scoped to the active tab URL
    if (targetUrl) {
      const direct = await chrome.cookies.get({
        url: targetUrl,
        name: "CAS_SESSION"
      });
      if (direct?.value) {
        return direct.value;
      }
    }

    // Fallback: query by domain and pick the best match
    const query = fallbackDomain ? { domain: fallbackDomain } : {};
    const cookies = await chrome.cookies.getAll(query);
    const candidates = cookies.filter(cookie => cookie.name === "CAS_SESSION");
    if (!candidates.length) {
      return null;
    }

    const best = pickBestCookie(candidates, targetUrl);
    return best ? best.value : null;
  } catch (error) {
    console.error("Error getting cookies:", error);
    throw new Error(`Failed to retrieve cookies: ${error.message}`);
  }
}

/**
 * Choose the most relevant CAS_SESSION cookie for the given URL.
 * Prefers hostOnly matches and paths that align with the URL, then newest expiration.
 * @param {chrome.cookies.Cookie[]} cookies
 * @param {string|undefined} url
 * @returns {chrome.cookies.Cookie|null}
 */
function pickBestCookie(cookies, url) {
  if (!url) {
    return cookies[0] ?? null;
  }

  let host = null;
  let path = "/";
  try {
    const parsed = new URL(url);
    host = parsed.hostname;
    path = parsed.pathname || "/";
  } catch (_) {
    return cookies[0] ?? null;
  }

  const scored = cookies.map(cookie => {
    let score = 0;
    const domainMatch = host && (host === cookie.domain.replace(/^\./, "") || host.endsWith(cookie.domain));
    const pathMatch = path.startsWith(cookie.path || "/");

    if (domainMatch) score += 5;
    if (cookie.hostOnly && domainMatch) score += 5;
    if (pathMatch) score += 2;
    if (cookie.expirationDate) score += cookie.expirationDate / 1e9; // normalize large numbers lightly

    return { cookie, score };
  });

  scored.sort((a, b) => b.score - a.score);
  return scored[0]?.cookie ?? null;
}

/**
 * Handle messages from popup and other extension components
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "GET_CAS") {
    getCasSession({ url: message.url, domain: message.domain })
      .then(value => {
        sendResponse({
          ok: true,
          casValue: value,
          message: value ? "CAS_SESSION found" : "CAS_SESSION not found"
        });
      })
      .catch(error => {
        sendResponse({
          ok: false,
          error: error.message
        });
      });

    return true; // async response
  }

  if (message.type === "COPY_TO_CLIPBOARD") {
    copyToClipboard(message.text)
      .then(() => {
        sendResponse({ ok: true, message: "Copied to clipboard" });
      })
      .catch(error => {
        sendResponse({ ok: false, error: error.message });
      });

    return true;
  }
});

/**
 * Copy text to clipboard using the Clipboard API
 * Falls back to offscreen document if needed
 * @param {string} text - Text to copy
 * @returns {Promise<void>}
 */
async function copyToClipboard(text) {
  try {
    // Try using the Clipboard API directly
    await navigator.clipboard.writeText(text);
  } catch (error) {
    // If direct access fails, use offscreen document when available
    console.log("Direct clipboard access failed, using offscreen document");
    await createOffscreenDocument();

    // Send message to offscreen document
    await chrome.runtime.sendMessage({
      type: "COPY_TEXT_OFFSCREEN",
      text: text,
      target: "offscreen"
    });
  }
}

/**
 * Create offscreen document for clipboard access
 */
async function createOffscreenDocument() {
  if (!chrome.offscreen) {
    throw new Error("Offscreen document API unavailable; allow clipboard access in the popup or update Chrome.");
  }

  // Check if offscreen document already exists
  if (chrome.offscreen.hasDocument && await chrome.offscreen.hasDocument()) {
    return;
  }

  // Create offscreen document
  await chrome.offscreen.createDocument({
    url: "offscreen.html",
    reasons: ["CLIPBOARD"],
    justification: "Copy CAS_SESSION to clipboard"
  });
}

// Service worker lifecycle management
chrome.runtime.onInstalled.addListener(() => {
  console.log("ByteDance SSO Auth Capture extension installed");
});

chrome.runtime.onStartup.addListener(() => {
  console.log("ByteDance SSO Auth Capture extension started");
});
