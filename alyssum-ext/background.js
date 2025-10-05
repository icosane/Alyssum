const ext = typeof browser !== 'undefined' ? browser : chrome;

if (ext.action && ext.action.onClicked) {
  // For Manifest V3 (Chrome)
  ext.action.onClicked.addListener(handleClick);
} else if (ext.browserAction && ext.browserAction.onClicked) {
  // For Manifest V2 (Firefox)
  ext.browserAction.onClicked.addListener(handleClick);
}

function handleClick(tab) {
  const url = tab.url || "";
  console.log("Extension icon clicked on:", url);

  if (url.endsWith(".pdf") || url.includes(".pdf?")) {
    const viewerUrl = ext.runtime.getURL("pdfjs/web/viewer.html") + "?file=" + encodeURIComponent(url);
    ext.tabs.create({ url: viewerUrl });
  } else {
    const viewerUrl = ext.runtime.getURL("pdfjs/web/viewer.html");
    ext.tabs.create({ url: viewerUrl });
  }
}

async function handleClick(tab) {
  const url = tab.url || "";
  console.log("Extension icon clicked on:", url);

  const viewerUrlBase = ext.runtime.getURL("pdfjs/web/viewer.html");

  // PDF file detected
  if (url.match(/\.pdf(\?|$)/i)) {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      const viewerUrl = `${viewerUrlBase}?file=${encodeURIComponent(blobUrl)}`;
      ext.tabs.create({ url: viewerUrl });
    } catch (err) {
      console.error("Failed to fetch PDF:", err);
      ext.tabs.create({ url: viewerUrlBase });
    }
  } else {
    // No PDF found, open blank viewer
    ext.tabs.create({ url: viewerUrlBase });
  }
}
