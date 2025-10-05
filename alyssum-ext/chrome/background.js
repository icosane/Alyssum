chrome.action.onClicked.addListener(async (tab) => {
  if (!tab || !tab.url) return;

  const url = tab.url;
  const viewerUrl = chrome.runtime.getURL("pdfjs/web/viewer.html");

  const looksLikePdf = (() => {
    try {
      const u = new URL(url);
      return u.pathname.toLowerCase().includes(".pdf");
    } catch {
      return url.toLowerCase().includes(".pdf");
    }
  })();

  async function isActuallyPdf(url) {
    try {
      const response = await fetch(url, { method: "HEAD" });
      const type = response.headers.get("Content-Type") || "";
      return type.includes("application/pdf");
    } catch {
      return false;
    }
  }

  let isPdf =
    looksLikePdf ||
    url.startsWith("blob:") ||
    url.startsWith("data:application/pdf");

  if (!isPdf && url.startsWith("http")) {
    isPdf = await isActuallyPdf(url);
  }

  if (isPdf) {
    const encodedUrl = encodeURIComponent(url);
    const fullViewerUrl = `${viewerUrl}?file=${encodedUrl}`;
    chrome.tabs.create({ url: fullViewerUrl });
  } else {
    chrome.tabs.create({ url: viewerUrl });
  }
});
