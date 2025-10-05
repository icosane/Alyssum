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
    "apiKey","serverPort","fontSize","bgColor","iconColor","autoTranslate","iconDelay"
  ]);
  settings = { ...settings, ...data };
  applyStyleSettings();
}

// --- Apply styles to button and tooltip ---
function applyStyleSettings() {
  if (tooltip) {
    tooltip.style.fontSize = settings.fontSize + "px";
    tooltip.style.background = settings.bgColor;
  }
  if (iconBtn) iconBtn.style.background = settings.iconColor || "#9332a3";
}

// --- Create floating icon ---
function makeIcon() {
    iconBtn = document.createElement("button");
    iconBtn.title = "Translate selection (Alyssum)";
    iconBtn.innerHTML = "✦";
    iconBtn.style.display = "none";
    iconBtn.style.position = "absolute";
    iconBtn.style.zIndex = 99999;
    iconBtn.style.fontSize = "16px";
    iconBtn.style.color = "#fff";
    iconBtn.style.background = settings.iconColor || "#9332a3";
    iconBtn.style.border = "none";
    iconBtn.style.cursor = "pointer";
    iconBtn.style.boxShadow = "0 2px 6px rgba(0,0,0,0.3)";
    
    // Force circular shape
    iconBtn.style.borderRadius = "50%";
    iconBtn.style.width = "32px";
    iconBtn.style.height = "32px";
    iconBtn.style.display = "flex";
    iconBtn.style.alignItems = "center";
    iconBtn.style.justifyContent = "center";
    iconBtn.style.padding = "0";
  
    iconBtn.addEventListener("click", onIconClick);
    document.body.appendChild(iconBtn);
  }
  

// --- Create tooltip ---
function makeTooltip() {
  tooltip = document.createElement("div");
  tooltip.style.display = "none";
  tooltip.style.position = "absolute";
  tooltip.style.zIndex = 99999;
  tooltip.style.fontSize = settings.fontSize + "px";
  tooltip.style.background = settings.bgColor;
  tooltip.style.color = "#fff";
  tooltip.style.padding = "4px 8px";
  tooltip.style.borderRadius = "4px";
  tooltip.style.boxShadow = "0 2px 6px rgba(0,0,0,0.3)";
  document.body.appendChild(tooltip);
}

// --- Selection utilities ---
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
  iconBtn.style.top = `${window.scrollY + rect.top - 30}px`;
  iconBtn.style.left = `${window.scrollX + rect.left}px`;
  iconBtn.style.display = "block";
}

function hideIcon() { if (iconBtn) iconBtn.style.display = "none"; }

function showTooltip(rect, text) {
  tooltip.innerText = text;
  const top = window.scrollY + rect.top - tooltip.offsetHeight - 10;
  const left = window.scrollX + rect.left;
  tooltip.style.top = `${top}px`;
  tooltip.style.left = `${left}px`;
  tooltip.style.display = "block";
}

// --- Translate selection ---
async function onIconClick(e) {
  e.stopPropagation();
  const info = getSelectionInfo();
  if (!info) return;
  translateAndShow(info);
}

async function translateAndShow(info) {
  if (!settings.apiKey) {
    showTooltip(info.rect, "API key not set. Please set it in options.");
    return;
  }

  const payload = { text: info.text, timeout: 8.0 };
  const url = `http://127.0.0.1:${settings.serverPort || 8765}/translate`;

  try {
    iconBtn.disabled = true;
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": settings.apiKey },
      body: JSON.stringify(payload),
      cache: "no-store"
    });
    const data = await resp.json();
    const translated = data.translated || "";
    try { await navigator.clipboard.writeText(translated); } catch {}
    showTooltip(info.rect, translated);
  } catch (err) {
    showTooltip(info.rect, "Connection error");
    console.error(err);
  } finally { iconBtn.disabled = false; }
}

// --- Selection change handler ---
function selectionChangedHandler() {
  clearTimeout(iconShowTimer);
  const info = getSelectionInfo();
  if (!info) { hideIcon(); return; }
  if (settings.autoTranslate) translateAndShow(info);
  else iconShowTimer = setTimeout(() => showIconAt(info.rect), (settings.iconDelay || 0) * 1000);
}

// --- Event listeners ---
document.addEventListener("selectionchange", () => setTimeout(selectionChangedHandler, 10));
document.addEventListener("mousedown", (e) => {
  if (tooltip && !tooltip.contains(e.target) && iconBtn && !iconBtn.contains(e.target)) {
    tooltip.style.display = "none";
    iconBtn.style.display = "none";
  }
});

// --- Initialization ---
function init() {
  if (!document.body) return;
  makeIcon();
  makeTooltip();
  loadSettings();
}

// Works for normal pages
document.addEventListener("DOMContentLoaded", init);

// Works for PDF.js viewer
// --- PDF.js load support for local or remote PDFs ---
document.addEventListener("webviewerloaded", async () => {
  init(); // initialize your floating icon & tooltip

  const params = new URLSearchParams(window.location.search);
  let fileParam = params.get("file");
  if (!fileParam) return;

  try {
    // Only fetch remote HTTP(S) URLs; blob/data/local URLs are loaded directly
    if (fileParam.startsWith("http://") || fileParam.startsWith("https://")) {
      const resp = await fetch(fileParam);
      if (!resp.ok) throw new Error("Failed to fetch PDF");
      const blob = await resp.blob();
      fileParam = URL.createObjectURL(blob); // WORKS inside the tab
    }

    // Load PDF.js document
    const loadingTask = pdfjsLib.getDocument(fileParam);
    const pdf = await loadingTask.promise;
    PDFViewerApplication.pdfDocument = pdf;
  } catch (err) {
    console.error("Failed to load PDF:", err);
    alert("Failed to load PDF. Check CORS or file URL permissions.");
  }
});


  
  

chrome.storage.onChanged.addListener(loadSettings);
