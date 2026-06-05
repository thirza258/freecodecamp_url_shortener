document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-copy-target]");
  if (!button) {
    return;
  }

  const target = document.querySelector(button.getAttribute("data-copy-target"));
  if (!target) {
    return;
  }

  try {
    await navigator.clipboard.writeText(target.textContent.trim());
    const original = button.textContent;
    button.textContent = "Copied";
    setTimeout(() => {
      button.textContent = original;
    }, 1200);
  } catch (_error) {
    button.textContent = "Copy failed";
  }
});
