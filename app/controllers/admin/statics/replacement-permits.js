document.querySelectorAll("[data-replacement-permit-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    const input = document.getElementById(button.dataset.replacementPermitCopy);
    if (!input) {
      return;
    }

    try {
      await navigator.clipboard.writeText(input.value);
    } catch {
      input.select();
      document.execCommand("copy");
      input.setSelectionRange(0, 0);
    }

    const originalLabel = button.textContent;
    button.textContent = "Copied";
    window.setTimeout(() => {
      button.textContent = originalLabel;
    }, 1500);
  });
});
