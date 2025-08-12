let iconBtn = null;
let tooltip = null;

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

  // Load settings
  const { apiKey, serverPort } = await chrome.storage.local.get(["apiKey", "serverPort"]);
  if (!apiKey) {
    showTooltip(info.rect, "API key not set. Please set it in extension options.");
    return;
  }

  const payload = { text: info.text, timeout: 8.0 };
  const url = `http://127.0.0.1:${serverPort || 8765}/translate`;

  try {
    iconBtn.disabled = true;
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey
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

    // Copy to clipboard
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
  const top = window.scrollY + rect.top - tooltip.offsetHeight - 10;
  const left = window.scrollX + rect.left;
  tooltip.style.top = `${top}px`;
  tooltip.style.left = `${left}px`;
  tooltip.style.display = "block";
}

function selectionChangedHandler() {
  const info = getSelectionInfo();
  if (!info) {
    hideIcon();
    return;
  }
  showIconAt(info.rect);
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
