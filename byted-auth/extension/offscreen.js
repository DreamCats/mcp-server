// Offscreen document for clipboard operations when direct access is restricted

/**
 * Handle messages from background script
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "COPY_TEXT_OFFSCREEN" && message.target === "offscreen") {
    copyTextToClipboard(message.text)
      .then(() => {
        sendResponse({ ok: true, message: "Text copied to clipboard" });
      })
      .catch(error => {
        sendResponse({ ok: false, error: error.message });
      });

    // Return true to indicate async response
    return true;
  }
});

/**
 * Copy text to clipboard using document.execCommand fallback
 * @param {string} text - Text to copy
 * @returns {Promise<void>}
 */
async function copyTextToClipboard(text) {
  try {
    // Try modern Clipboard API first
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }

    // Fallback to document.execCommand
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
      const successful = document.execCommand('copy');
      if (!successful) {
        throw new Error('Copy command failed');
      }
    } finally {
      document.body.removeChild(textArea);
    }

  } catch (error) {
    throw new Error(`Failed to copy text: ${error.message}`);
  }
}