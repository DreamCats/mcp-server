// Popup script for ByteDance SSO Auth Capture extension

// Domain and login URL mappings for different regions
const DOMAIN_MAP = {
  cn: "https://cloud.bytedance.net",
  us: "https://cloud-ttp-us.bytedance.net", // Can be changed to .bytedance.com if needed
  i18n: "https://cloud-i18n.bytedance.net",
};

const LOGIN_URL_MAP = {
  cn: "https://cloud.bytedance.net/auth/api/v1/login",
  us: "https://cloud-ttp-us.bytedance.net/auth/api/v1/login",
  i18n: "https://cloud-i18n.bytedance.net/auth/api/v1/login",
};

// Global state
let currentRegion = null;
let currentCasValue = null;

/**
 * Detect region from URL based on login URL patterns
 * @param {string} url - Current page URL
 * @returns {string|null} Detected region (cn/us/i18n) or null if not recognized
 */
function detectRegionFromUrl(url) {
  if (!url) return null;

  try {
    // Check for specific region patterns in the URL
    if (url.includes(LOGIN_URL_MAP.us)) {
      return 'us';
    } else if (url.includes(LOGIN_URL_MAP.i18n)) {
      return 'i18n';
    } else if (url.includes(LOGIN_URL_MAP.cn)) {
      return 'cn';
    }

    return null;
  } catch (error) {
    console.error('Error detecting region from URL:', error);
    return null;
  }
}

/**
 * Initialize popup when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', async () => {
  await initializePopup();
  setupEventListeners();
});

/**
 * Initialize popup with current tab information
 */
async function initializePopup() {
  try {
    // Get current tab information
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const statusElement = document.getElementById('current-status');

    if (tab && tab.url) {
      // Check if current page is a ByteDance SSO login page
      if (tab.url.includes(LOGIN_URL_MAP.cn) || tab.url.includes(LOGIN_URL_MAP.us) || tab.url.includes(LOGIN_URL_MAP.i18n)) {
        // Analyze URL to determine which region this page belongs to
        const detectedRegion = detectRegionFromUrl(tab.url);

        if (detectedRegion) {
          statusElement.textContent = `当前页面: ${detectedRegion.toUpperCase()}区域 SSO登录页，点击对应区域按钮提取CAS_SESSION`;
          // Highlight the detected region button
          highlightRegionButton(detectedRegion);
        } else {
          statusElement.textContent = `当前页面: SSO登录页，点击区域按钮提取CAS_SESSION`;
        }
      } else {
        statusElement.textContent = '当前页面不是SSO登录页，点击区域按钮开始登录流程';
      }
    } else {
      statusElement.textContent = '无法获取当前页面信息';
    }

    // Load saved region preference (only if no region detected from URL)
    const detectedRegion = detectRegionFromUrl(tab?.url || '');
    if (!detectedRegion) {
      const savedRegion = await loadSavedRegion();
      if (savedRegion) {
        highlightRegionButton(savedRegion);
      }
    }

  } catch (error) {
    console.error('Error initializing popup:', error);
    showStatus('Error initializing popup', 'error');
  }
}

/**
 * Setup event listeners for UI elements
 */
function setupEventListeners() {
  // Region button listeners
  document.querySelectorAll('.region-btn').forEach(button => {
    button.addEventListener('click', handleRegionClick);
  });

  // Copy button listener
  document.getElementById('copy-btn').addEventListener('click', handleCopyClick);
}

/**
 * Handle region button click - Smart logic: check current page first
 * @param {Event} event - Click event
 */
async function handleRegionClick(event) {
  const region = event.target.dataset.region;

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const detectedRegion = tab?.url ? detectRegionFromUrl(tab.url) : null;

  // Only bypass navigation when当前页确实属于目标区域
  if (tab && tab.url && detectedRegion === region) {
    showStatus('检测到当前页面属于该区域 SSO，正在提取CAS_SESSION...', 'info');
    await fetchCasForRegion(region);
    return;
  }

  // Otherwise open the target region login page
  await navigateToSSOLogin(region);
}

/**
 * Navigate to SSO login page in new tab
 * @param {string} region - Region identifier (cn/us/i18n)
 */
async function navigateToSSOLogin(region) {
  try {
    // Update UI state
    currentRegion = region;
    currentCasValue = null;
    highlightRegionButton(region);
    showLoading();
    saveRegionPreference(region);

    // Get login URL for region
    const loginUrl = LOGIN_URL_MAP[region];

    // Create new tab for SSO login page
    await chrome.tabs.create({ url: loginUrl });

    // Show message and close popup
    showStatus('已在新标签页打开SSO登录页，请完成登录后重新打开扩展', 'info');

    // Close popup after a short delay to show the message
    setTimeout(() => {
      window.close();
    }, 1500);

  } catch (error) {
    console.error('Error navigating to SSO login:', error);
    displayError(error.message);
  }
}

// Removed checkMonitoringStatus - no longer needed

/**
 * Fetch CAS_SESSION for specified region (legacy function for direct extraction)
 * @param {string} region - Region identifier (cn/us/i18n)
 */
async function fetchCasForRegion(region) {
  try {
    // Update UI state
    currentRegion = region;
    currentCasValue = null;
    highlightRegionButton(region);
    showLoading();
    saveRegionPreference(region);

    // Get domain and URL for region
    const domain = DOMAIN_MAP[region];
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const targetUrl = tab?.url && tab.url.startsWith('http') ? tab.url : LOGIN_URL_MAP[region];

    // Send message to background script with precise URL to avoid cross-domain mismatches
    const response = await chrome.runtime.sendMessage({
      type: "GET_CAS",
      domain: domain,
      url: targetUrl
    });

    if (response.ok) {
      currentCasValue = response.casValue;
      displayResult(region, response.casValue, response.message);
      updateCopyButtonState();
    } else {
      throw new Error(response.error || 'Failed to get CAS_SESSION');
    }

  } catch (error) {
    console.error('Error fetching CAS_SESSION:', error);
    displayError(error.message);
  }
}

/**
 * Handle copy button click
 */
async function handleCopyClick() {
  if (!currentCasValue) {
    showStatus('No CAS_SESSION to copy', 'error');
    return;
  }

  // Try copying directly from the popup first
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(currentCasValue);
      showStatus('Copied to clipboard!', 'success');
      const copyBtn = document.getElementById('copy-btn');
      const originalText = copyBtn.textContent;
      copyBtn.textContent = 'Copied!';
      setTimeout(() => {
        copyBtn.textContent = originalText;
      }, 2000);
      return;
    }
  } catch (err) {
    console.warn('Popup clipboard write failed, falling back to background:', err);
  }

  try {
    // Send copy request to background script
    const response = await chrome.runtime.sendMessage({
      type: "COPY_TO_CLIPBOARD",
      text: currentCasValue
    });

    if (response.ok) {
      showStatus('Copied to clipboard!', 'success');
      // Temporarily change button text
      const copyBtn = document.getElementById('copy-btn');
      const originalText = copyBtn.textContent;
      copyBtn.textContent = 'Copied!';
      setTimeout(() => {
        copyBtn.textContent = originalText;
      }, 2000);
    } else {
      throw new Error(response.error || 'Failed to copy to clipboard');
    }

  } catch (error) {
    console.error('Error copying to clipboard:', error);
    showStatus(`Copy failed: ${error.message}`, 'error');
  }
}

/**
 * Display CAS_SESSION result
 * @param {string} region - Selected region
 * @param {string|null} casValue - CAS_SESSION value
 * @param {string} message - Status message
 */
function displayResult(region, casValue, message) {
  const casValueElement = document.getElementById('cas-value');
  const selectedRegionElement = document.getElementById('selected-region');
  const loginUrlElement = document.getElementById('login-url');

  // Update region tag
  selectedRegionElement.textContent = region.toUpperCase();
  selectedRegionElement.classList.remove('hidden');

  // Update CAS value display
  if (casValue) {
    casValueElement.textContent = casValue;
    casValueElement.classList.remove('empty');
  } else {
    casValueElement.textContent = '(未找到 CAS_SESSION)';
    casValueElement.classList.add('empty');
  }

  // Update login URL
  loginUrlElement.textContent = `Login URL: ${LOGIN_URL_MAP[region]}`;
  loginUrlElement.classList.remove('hidden');

  // Update status
  showStatus(message, casValue ? 'success' : 'warning');
}

/**
 * Display error message
 * @param {string} errorMessage - Error message to display
 */
function displayError(errorMessage) {
  const casValueElement = document.getElementById('cas-value');
  const selectedRegionElement = document.getElementById('selected-region');
  const loginUrlElement = document.getElementById('login-url');

  // Hide region info
  selectedRegionElement.classList.add('hidden');
  loginUrlElement.classList.add('hidden');

  // Display error
  casValueElement.textContent = `错误: ${errorMessage}`;
  casValueElement.classList.add('empty');

  // Update status
  showStatus('Error occurred', 'error');
  updateCopyButtonState();
}

/**
 * Show loading state
 */
function showLoading() {
  const casValueElement = document.getElementById('cas-value');
  casValueElement.innerHTML = '<span class="loading"></span>正在处理...';
  casValueElement.classList.remove('empty');
  showStatus('正在处理请求...', 'info');
}

/**
 * Highlight active region button
 * @param {string} region - Active region
 */
function highlightRegionButton(region) {
  // Remove active class from all buttons
  document.querySelectorAll('.region-btn').forEach(btn => {
    btn.classList.remove('active');
  });

  // Add active class to selected button
  const activeButton = document.getElementById(`btn-${region}`);
  if (activeButton) {
    activeButton.classList.add('active');
  }
}

/**
 * Update copy button state based on CAS value
 */
function updateCopyButtonState() {
  const copyBtn = document.getElementById('copy-btn');
  copyBtn.disabled = !currentCasValue;
}

/**
 * Show status message
 * @param {string} message - Status message
 * @param {string} type - Message type (success/error/warning/info)
 */
function showStatus(message, type = 'info') {
  const statusElement = document.getElementById('status');
  statusElement.textContent = message;
  statusElement.className = `status ${type}`;
}

/**
 * Save region preference to storage
 * @param {string} region - Selected region
 */
async function saveRegionPreference(region) {
  try {
    await chrome.storage.local.set({ lastSelectedRegion: region });
  } catch (error) {
    console.warn('Failed to save region preference:', error);
  }
}

/**
 * Load saved region preference from storage
 * @returns {Promise<string|null>} Saved region or null
 */
async function loadSavedRegion() {
  try {
    const result = await chrome.storage.local.get(['lastSelectedRegion']);
    return result.lastSelectedRegion || null;
  } catch (error) {
    console.warn('Failed to load region preference:', error);
    return null;
  }
}
