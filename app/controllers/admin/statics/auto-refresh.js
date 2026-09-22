(() => {
  const toolbar = document.querySelector("[data-auto-refresh]");
  if (!toolbar) {
    return;
  }

  const toggle = toolbar.querySelector("[data-auto-refresh-toggle]");
  const status = toolbar.querySelector("[data-auto-refresh-status]");
  const selector = toolbar.querySelector("[data-auto-refresh-interval]");
  const pauseKey = "farang-admin-auto-refresh-paused";
  const intervalKey = "farang-admin-auto-refresh-interval";
  const intervals = [5, 10, 30];
  let interval = 30_000;
  let paused = false;
  let dirty = false;

  try {
    paused = window.sessionStorage.getItem(pauseKey) === "true";
    const savedInterval = Number(window.sessionStorage.getItem(intervalKey));
    if (intervals.includes(savedInterval)) {
      interval = savedInterval * 1000;
    }
  } catch {
    // Refresh still works when browser storage is unavailable.
  }
  selector.value = String(interval / 1000);
  let nextRefresh = Date.now() + interval;

  function isBusy() {
    return (
      dirty ||
      document.querySelector(
        ".select-box:checked, #select-all:checked, .modal.show, .dropdown-menu.show",
      ) ||
      (!toolbar.contains(document.activeElement) &&
        document.activeElement?.matches(
          "input, textarea, select, [contenteditable]:not([contenteditable='false'])",
        )) ||
      window.getSelection()?.toString().length > 0
    );
  }

  function update() {
    const waiting = document.hidden || isBusy();
    if (paused || waiting) {
      nextRefresh = Date.now() + interval;
    }

    toggle.textContent = paused ? "Resume auto-refresh" : "Pause auto-refresh";
    toggle.setAttribute("aria-pressed", String(paused));
    if (paused) {
      status.textContent = "Auto-refresh paused";
    } else if (waiting) {
      status.textContent = "Auto-refresh waiting for this page to be idle";
    } else {
      const remaining = Math.max(0, Math.ceil((nextRefresh - Date.now()) / 1000));
      status.textContent = `Refreshing in ${remaining}s`;
      if (remaining === 0) {
        // Reload the current URL, retaining pagination and other query parameters.
        nextRefresh = Date.now() + interval;
        window.location.reload();
      }
    }
  }

  toggle.addEventListener("click", () => {
    paused = !paused;
    nextRefresh = Date.now() + interval;
    try {
      window.sessionStorage.setItem(pauseKey, String(paused));
    } catch {
      // Keep the toggle usable even without storage.
    }
    update();
  });

  selector.addEventListener("change", () => {
    const seconds = Number(selector.value);
    if (!intervals.includes(seconds)) {
      return;
    }
    interval = seconds * 1000;
    nextRefresh = Date.now() + interval;
    try {
      window.sessionStorage.setItem(intervalKey, String(seconds));
    } catch {
      // Keep the selector usable even without storage.
    }
    update();
  });

  document.addEventListener("input", (event) => {
    if (
      !toolbar.contains(event.target) &&
      event.target.matches(
        "input:not([type='checkbox']), textarea, select, [contenteditable]",
      )
    ) {
      dirty = true;
    }
  });
  document.addEventListener("visibilitychange", () => {
    nextRefresh = Date.now() + interval;
    update();
  });

  toolbar.hidden = false;
  update();
  window.setInterval(update, 1000);
})();
