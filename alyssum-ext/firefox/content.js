let iconBtn = null;
let tooltip = null;
let settings = {
  apiKey: "",
  serverPort: "8765",
  fontSize: 14,
  bgColor: "#000000",
  iconColor: "#9332a3",
  autoTranslate: false,
  iconDelay: 0
};

let iconShowTimer = null;

function getStorage(keys) {
  return new Promise(resolve => chrome.storage.local.get(keys, resolve));
}

function setStorage(items) {
  return new Promise(resolve => chrome.storage.local.set(items, resolve));
}

// --- Load settings ---
async function loadSettings() {
  const data = await getStorage([
    "apiKey", "serverPort", "fontSize", "bgColor", "iconColor", "autoTranslate", "iconDelay"
  ]);
  settings = { ...settings, ...data };
  applyStyleSettings();
}

function applyStyleSettings() {
  if (tooltip) {
    tooltip.style.fontSize = settings.fontSize + "px";
    tooltip.style.background = settings.bgColor;
  }
  if (iconBtn) {
    iconBtn.style.background = settings.iconColor;
  }
}

function makeIcon() {
  iconBtn = document.createElement("button");
  iconBtn.className = "alyssum-float-button";
  iconBtn.title = "Translate selection (Alyssum)";
  iconBtn.innerHTML = "✦";
  iconBtn.style.display = "none";
  iconBtn.addEventListener("click", onIconClick);
  document.body.appendChild(iconBtn);
}

function makeTooltip() {
  tooltip = document.createElement("div");
  tooltip.className = "alyssum-tooltip";
  tooltip.style.display = "none";
  document.body.appendChild(tooltip);
}

function getSelectionInfo() {
  const sel = window.getSelection();
  if (!sel || sel.isCollapsed) return null;
  const text = sel.toString().trim();
  if (!text) return null;
  const range = sel.getRangeAt(0).cloneRange();
  const rect = range.getBoundingClientRect();
  return { text, rect, range };
}

function showIconAt(rect) {
  const top = window.scrollY + rect.top - 30;
  const left = window.scrollX + rect.left;
  iconBtn.style.top = `${top}px`;
  iconBtn.style.left = `${left}px`;
  iconBtn.style.display = "block";
}

function hideIcon() {
  if (iconBtn) iconBtn.style.display = "none";
}

async function onIconClick(e) {
  e.stopPropagation();
  const info = getSelectionInfo();
  if (!info) return;
  translateAndShow(info);
}

async function translateAndShow(info) {
  if (!settings.apiKey) {
    showTooltip(info.rect, "API key not set. Please set it in extension options.");
    return;
  }

  const payload = { text: info.text, timeout: 8.0 };
  const url = `http://127.0.0.1:${settings.serverPort || 8765}/translate`;

  try {
    iconBtn.disabled = true;
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": settings.apiKey
      },
      body: JSON.stringify(payload),
      cache: "no-store"
    });

    if (!resp.ok) {
      const body = await resp.json().catch(()=>({}));
      showTooltip(info.rect, "Error: " + (body.error || resp.statusText));
      iconBtn.disabled = false;
      return;
    }
    const data = await resp.json();
    const translated = data.translated || "";

    try {
      await navigator.clipboard.writeText(translated);
    } catch (err) {
      console.warn("Clipboard write failed:", err);
    }

    showTooltip(info.rect, translated);
  } catch (err) {
    showTooltip(info.rect, "Connection error");
    console.error(err);
  } finally {
    iconBtn.disabled = false;
  }
}

function showTooltip(rect, text) {
  tooltip.innerText = text;
  tooltip.style.fontSize = settings.fontSize + "px";
  tooltip.style.background = settings.bgColor;
  const top = window.scrollY + rect.top - tooltip.offsetHeight - 10;
  const left = window.scrollX + rect.left;
  tooltip.style.top = `${top}px`;
  tooltip.style.left = `${left}px`;
  tooltip.style.display = "block";
}

function selectionChangedHandler() {
  clearTimeout(iconShowTimer);
  const info = getSelectionInfo();
  if (!info) {
    hideIcon();
    return;
  }
  if (settings.autoTranslate) {
    translateAndShow(info);
  } else {
    iconShowTimer = setTimeout(() => {
      showIconAt(info.rect);
    }, (settings.iconDelay || 0) * 1000);
  }
}

document.addEventListener("selectionchange", () => {
  setTimeout(selectionChangedHandler, 10);
});

document.addEventListener("mousedown", (e) => {
  if (
    tooltip && !tooltip.contains(e.target) &&
    iconBtn && !iconBtn.contains(e.target)
  ) {
    tooltip.style.display = "none";
    iconBtn.style.display = "none";
  }
});

makeIcon();
makeTooltip();
loadSettings();
chrome.storage.onChanged.addListener(loadSettings);
