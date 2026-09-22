const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { resolve } = require("node:path");
const { test } = require("node:test");
const { runInNewContext } = require("node:vm");

const script = readFileSync(
  resolve(__dirname, "../app/controllers/admin/statics/auto-refresh.js"),
  "utf8",
);
const pauseKey = "farang-admin-auto-refresh-paused";
const intervalKey = "farang-admin-auto-refresh-interval";

function page({ saved = {}, storageFails = false, enabled = true } = {}) {
  let now = 0;
  let tick;
  let reloads = 0;
  const stored = new Map(Object.entries(saved));
  const element = () => ({
    events: {},
    attributes: {},
    addEventListener(name, handler) { this.events[name] = handler; },
    setAttribute(name, value) { this.attributes[name] = value; },
  });
  const toggle = element();
  const selector = element();
  const status = element();
  const toolbar = {
    querySelector: (query) => ({
      "[data-auto-refresh-toggle]": toggle,
      "[data-auto-refresh-interval]": selector,
      "[data-auto-refresh-status]": status,
    })[query],
    contains: (target) => [toggle, selector, status].includes(target),
  };
  const document = {
    ...element(),
    hidden: false,
    activeElement: null,
    blocker: null,
    querySelector(query) {
      if (query === "[data-auto-refresh]") return enabled ? toolbar : null;
      // Match each SQLAdmin interaction against the production selectors.
      return query.split(", ").includes(this.blocker) ? {} : null;
    },
  };
  const window = {
    sessionStorage: {
      getItem(key) {
        if (storageFails) throw new Error("Storage blocked");
        return stored.get(key) ?? null;
      },
      setItem(key, value) {
        if (storageFails) throw new Error("Storage blocked");
        stored.set(key, value);
      },
    },
    location: {
      href: "https://example.test/admin/engine-projection/list?page=2&pageSize=10",
      reload() { reloads++; },
    },
    selection: "",
    getSelection() { return this.selection; },
    setInterval(callback, delay) {
      assert.equal(delay, 1000);
      tick = callback;
    },
  };
  runInNewContext(script, { window, document, Date: { now: () => now } });
  return {
    document, window, toggle, selector, status, stored,
    get reloads() { return reloads; },
    get scheduled() { return Boolean(tick); },
    advance(seconds) {
      for (let i = 0; i < seconds; i++) { now += 1000; tick(); }
    },
    choose(seconds) { selector.value = String(seconds); selector.events.change(); },
  };
}

test("default refresh reloads the current URL after 30 seconds", () => {
  const p = page();
  p.advance(29);
  assert.equal(p.reloads, 0);
  assert.equal(p.status.textContent, "Refreshing in 1s");
  p.advance(1);
  assert.equal(p.reloads, 1);
  assert.equal(p.window.location.href, "https://example.test/admin/engine-projection/list?page=2&pageSize=10");
  p.advance(1);
  assert.equal(p.reloads, 1);
});

for (const interval of [5, 10, 30]) {
  test(`choosing ${interval}s starts a fresh countdown and survives navigation`, () => {
    const p = page();
    p.advance(4);
    p.choose(interval);
    p.document.activeElement = p.selector;
    p.document.events.input({ target: p.selector });
    p.advance(interval - 1);
    assert.equal(p.reloads, 0);
    p.advance(1);
    assert.equal(p.reloads, 1);
    const next = page({ saved: Object.fromEntries(p.stored) });
    assert.equal(next.selector.value, String(interval));
    next.advance(interval);
    assert.equal(next.reloads, 1);
  });
}

test("pause persists and resume waits a full selected interval", () => {
  const p = page();
  p.choose(5);
  p.toggle.events.click();
  p.advance(60);
  assert.equal(p.reloads, 0);
  assert.equal(p.toggle.attributes["aria-pressed"], "true");
  const next = page({ saved: Object.fromEntries(p.stored) });
  next.advance(60);
  assert.equal(next.reloads, 0);
  next.toggle.events.click();
  next.advance(4);
  assert.equal(next.reloads, 0);
  next.advance(1);
  assert.equal(next.reloads, 1);
  assert.equal(next.stored.get(pauseKey), "false");
});

for (const blocker of [".select-box:checked", "#select-all:checked", ".modal.show", ".dropdown-menu.show"]) {
  test(`refresh waits for ${blocker} to clear`, () => {
    const p = page({ saved: { [intervalKey]: "5" } });
    p.document.blocker = blocker;
    p.advance(10);
    assert.equal(p.reloads, 0);
    p.document.blocker = null;
    p.advance(4);
    assert.equal(p.reloads, 0);
    p.advance(1);
    assert.equal(p.reloads, 1);
  });
}

test("hidden tabs restart their countdown when visible", () => {
  const p = page();
  p.document.hidden = true;
  p.advance(60);
  assert.equal(p.reloads, 0);
  p.document.hidden = false;
  p.document.events.visibilitychange();
  p.advance(29);
  assert.equal(p.reloads, 0);
  p.advance(1);
  assert.equal(p.reloads, 1);
});

test("focused inputs and selected text postpone reload", () => {
  const p = page();
  p.document.activeElement = { matches: () => true };
  p.advance(60);
  assert.equal(p.reloads, 0);
  p.document.activeElement = null;
  p.window.selection = "engine config";
  p.advance(60);
  assert.equal(p.reloads, 0);
  p.window.selection = "";
  p.advance(30);
  assert.equal(p.reloads, 1);
});

test("changed inputs remain protected after losing focus", () => {
  const p = page();
  p.document.events.input({ target: { matches: () => true } });
  p.advance(60);
  assert.equal(p.reloads, 0);
});

test("unavailable storage does not break controls", () => {
  const p = page({ storageFails: true });
  p.choose(5);
  p.toggle.events.click();
  p.advance(10);
  assert.equal(p.reloads, 0);
  p.toggle.events.click();
  p.advance(5);
  assert.equal(p.reloads, 1);
});

test("invalid stored intervals fall back to 30 seconds", () => {
  const p = page({ saved: { [intervalKey]: "1" } });
  assert.equal(p.selector.value, "30");
  p.advance(30);
  assert.equal(p.reloads, 1);
});

test("pages without the refresh toolbar never schedule reloads", () => {
  assert.equal(page({ enabled: false }).scheduled, false);
});
