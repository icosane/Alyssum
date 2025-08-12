document.addEventListener("DOMContentLoaded", async () => {
    const apiKeyInput = document.getElementById("apiKey");
    const portInput = document.getElementById("serverPort");
    const statusEl = document.getElementById("status");
  
    // Load saved settings
    const data = await chrome.storage.local.get(["apiKey", "serverPort"]);
    if (data.apiKey) apiKeyInput.value = data.apiKey;
    if (data.serverPort) portInput.value = data.serverPort;
  
    document.getElementById("save").addEventListener("click", async () => {
      const apiKey = apiKeyInput.value.trim();
      const serverPort = portInput.value.trim() || "8765";
  
      await chrome.storage.local.set({ apiKey, serverPort });
  
      statusEl.textContent = "Settings saved!";
      setTimeout(() => { statusEl.textContent = ""; }, 2000);
    });
  });
  