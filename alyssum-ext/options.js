document.addEventListener("DOMContentLoaded", () => {
  const DEFAULTS = {
    fontSize: 14,
    bgColor: "#000000",
    iconColor: "#9332a3",
    iconDelay: 0
  };

  const apiKeyInput = document.getElementById("apiKey");
  const portInput = document.getElementById("serverPort");
  const fontSizeInput = document.getElementById("fontSize");
  const bgColorInput = document.getElementById("bgColor");
  const iconColorInput = document.getElementById("iconColor");
  const iconDelayInput = document.getElementById("iconDelay");
  const statusEl = document.getElementById("status");

  const previewIcon = document.getElementById("preview-icon");
  const previewTooltip = document.getElementById("preview-tooltip");

  const resetBgBtn = document.getElementById("resetBgColor");
  const resetIconBtn = document.getElementById("resetIconColor");

  // --- helper for async storage in Firefox MV2 ---
  function getStorage(keys) {
    return new Promise(resolve => chrome.storage.local.get(keys, resolve));
  }

  function setStorage(items) {
    return new Promise(resolve => chrome.storage.local.set(items, resolve));
  }

  // Load saved settings
  getStorage([
    "apiKey", "serverPort", "fontSize", "bgColor", "iconColor", "iconDelay"
  ]).then(data => {
    apiKeyInput.value = data.apiKey || "";
    portInput.value = data.serverPort || "8765";
    fontSizeInput.value = data.fontSize || DEFAULTS.fontSize;
    bgColorInput.value = data.bgColor || DEFAULTS.bgColor;
    iconColorInput.value = data.iconColor || DEFAULTS.iconColor;
    iconDelayInput.value = data.iconDelay ?? DEFAULTS.iconDelay;

    updatePreview();
  });

  // Live update preview on change
  fontSizeInput.addEventListener("input", updatePreview);
  bgColorInput.addEventListener("input", updatePreview);
  iconColorInput.addEventListener("input", updatePreview);
  iconDelayInput.addEventListener("input", updatePreview);

  // Reset buttons
  resetBgBtn.addEventListener("click", () => {
    bgColorInput.value = DEFAULTS.bgColor;
    updatePreview();
  });
  resetIconBtn.addEventListener("click", () => {
    iconColorInput.value = DEFAULTS.iconColor;
    updatePreview();
  });

  function updatePreview() {
    const fontSize = parseInt(fontSizeInput.value.trim()) || DEFAULTS.fontSize;
    const bgColor = bgColorInput.value.trim() || DEFAULTS.bgColor;
    const iconColor = iconColorInput.value.trim() || DEFAULTS.iconColor;

    previewTooltip.style.fontSize = fontSize + "px";
    previewTooltip.style.background = bgColor;
    previewIcon.style.background = iconColor;
  }

  // Save button
  document.getElementById("save").addEventListener("click", () => {
    const apiKey = apiKeyInput.value.trim();
    const serverPort = portInput.value.trim() || "8765";
    const fontSize = parseInt(fontSizeInput.value.trim()) || DEFAULTS.fontSize;
    const bgColor = bgColorInput.value.trim() || DEFAULTS.bgColor;
    const iconColor = iconColorInput.value.trim() || DEFAULTS.iconColor;
    const iconDelay = parseFloat(iconDelayInput.value.trim()) || DEFAULTS.iconDelay;

    setStorage({ apiKey, serverPort, fontSize, bgColor, iconColor, iconDelay }).then(() => {
      statusEl.textContent = "Settings saved!";
      setTimeout(() => { statusEl.textContent = ""; }, 2000);
    });
  });
});
