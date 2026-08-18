document.addEventListener("DOMContentLoaded", () => {
  // Toast helper
  function showToast(message) {
    let toast = document.getElementById("siteToast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "siteToast";
      toast.className = "copied-toast";
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 2000);
  }

  // Copy-to-clipboard buttons
  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy-target]");
    if (!button) {
      return;
    }

    const targetSelector = button.getAttribute("data-copy-target");
    const target = document.querySelector(targetSelector);
    if (!target) {
      return;
    }

    const textToCopy = target.value ? target.value.trim() : target.textContent.trim();
    if (!textToCopy) {
      return;
    }

    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(textToCopy);
      } else {
        // Fallback for non-https or older browser environments
        const textArea = document.createElement("textarea");
        textArea.value = textToCopy;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        textArea.style.top = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand("copy");
        textArea.remove();
      }

      if (!button.hasAttribute("data-original-html")) {
        button.setAttribute("data-original-html", button.innerHTML);
      }
      const originalHtml = button.getAttribute("data-original-html");
      button.innerHTML = "<span>✓ Copied!</span>";
      button.classList.add("btn-success");
      showToast("Short link copied to clipboard!");

      setTimeout(() => {
        button.innerHTML = originalHtml;
        button.classList.remove("btn-success");
      }, 1800);
    } catch (_error) {
      showToast("Unable to copy automatically.");
    }
  });

  // Paste helper button for original URL input
  const pasteBtn = document.getElementById("btnPasteUrl");
  const originalUrlInput = document.getElementById("id_original_url");
  if (pasteBtn && originalUrlInput && navigator.clipboard && navigator.clipboard.readText) {
    pasteBtn.addEventListener("click", async () => {
      try {
        const text = await navigator.clipboard.readText();
        if (text && (text.startsWith("http://") || text.startsWith("https://"))) {
          originalUrlInput.value = text.trim();
          originalUrlInput.focus();
          showToast("URL pasted from clipboard!");
        } else if (text) {
          originalUrlInput.value = text.trim();
          originalUrlInput.focus();
        }
      } catch (_err) {
        originalUrlInput.focus();
      }
    });
  }

  // QR Download helper
  const qrDownloadBtn = document.getElementById("btnDownloadQr");
  const qrImage = document.querySelector(".qr-code-image, .qr-code");
  if (qrDownloadBtn && qrImage && qrImage.src) {
    qrDownloadBtn.addEventListener("click", () => {
      const link = document.createElement("a");
      link.href = qrImage.src;
      link.download = `qr-code-${Date.now()}.png`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      showToast("QR Code downloaded!");
    });
  }
});
