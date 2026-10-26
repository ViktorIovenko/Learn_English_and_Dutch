/* ParallelLingvo ads client (Free plan only).
 * The server decides everything (/api/ads/page): mode, plan, child account,
 * consent and material. This script only renders what it receives, with DOM
 * node APIs and textContent only, and never loads third-party scripts.
 */
(function () {
  "use strict";
  const slots = Array.from(document.querySelectorAll("[data-ad-placement]"));

  function device() {
    const w = window.innerWidth || document.documentElement.clientWidth || 360;
    return w < 600 ? "phone" : w < 1024 ? "tablet" : "desktop";
  }
  function platform() {
    const tg = window.Telegram && window.Telegram.WebApp;
    return tg && tg.initData ? "telegram" : "web";
  }
  function el(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text) node.textContent = text;
    return node;
  }
  function beacon(payload) {
    const body = JSON.stringify(Object.assign({device: device()}, payload));
    const url = "/api/ads/event?platform=" + platform();
    try {
      if (navigator.sendBeacon && navigator.sendBeacon(url, new Blob([body], {type: "application/json"}))) return;
    } catch (e) { /* fall back to fetch */ }
    fetch(url, {method: "POST", credentials: "same-origin", keepalive: true,
      headers: {"Content-Type": "application/json"}, body}).catch(() => {});
  }
  async function saveConsent(choice) {
    const resp = await fetch("/api/ads/consent", {
      method: "POST", credentials: "same-origin",
      headers: {"Content-Type": "application/json"}, body: JSON.stringify({choice}),
    });
    return resp.ok;
  }

  // ---- settings page consent controls -----------------------------------
  const consentState = document.getElementById("ads-consent-state");
  document.querySelectorAll("[data-ads-consent]").forEach((button) => {
    button.addEventListener("click", async () => {
      const ok = await saveConsent(button.dataset.adsConsent).catch(() => false);
      if (consentState) consentState.textContent = ok ? "✓" : "⚠";
      if (ok) load();
    });
  });

  // ---- rendering -----------------------------------------------------------
  function renderSlot(host, slot) {
    host.replaceChildren();
    // Keep the position chosen by placeBetween (it may run before rendering).
    const position = ["ad-slot--in-grid", "ad-slot--in-cell"].filter((c) => host.classList.contains(c));
    host.className = "ad-slot ad-slot--filled ad-slot--" + slot.render + (slot.preview ? " ad-slot--preview" : "");
    position.forEach((c) => host.classList.add(c));
    host.style.setProperty("--ad-w", slot.width + "px");
    host.style.setProperty("--ad-h", slot.height + "px");
    host.dataset.adSize = slot.size;
    host.setAttribute("aria-label", slot.label);
    const label = el("span", "ad-slot__label", slot.label);
    const frame = el("div", "ad-slot__frame");
    if (slot.render === "placeholder") {
      // Admin simulation only: an outlined, switched-off ad position.
      const box = el("div", "ad-slot__card ad-slot__placeholder");
      const copy = el("div", "ad-slot__copy");
      copy.append(el("strong", "ad-slot__headline", slot.headline + " · " + slot.size),
        el("span", "ad-slot__body", slot.body || ""));
      box.append(copy);
      frame.append(box);
    } else if (slot.render === "image") {
      const link = el("a", "ad-slot__link");
      link.href = slot.click_url;
      link.target = "_blank";
      link.rel = "sponsored noopener noreferrer";
      const img = el("img", "ad-slot__img");
      img.src = slot.image_url;
      img.width = slot.width; img.height = slot.height;
      img.alt = slot.alt || "";
      img.loading = "lazy";
      img.referrerPolicy = "origin";
      img.addEventListener("error", () => { host.hidden = true; });
      link.append(img);
      link.addEventListener("click", () => beacon({event: "click", placement: slot.placement, creative_id: slot.creative_id}));
      frame.append(link);
    } else {
      // demo / mock (admin simulation) and LIVE text ads share one layout.
      const card = el(slot.render === "text" ? "a" : "div", "ad-slot__card ad-tone--" + (slot.tone || "violet"));
      if (slot.render === "text") {
        card.href = slot.click_url; card.target = "_blank"; card.rel = "sponsored noopener noreferrer";
        card.addEventListener("click", () => beacon({event: "click", placement: slot.placement, creative_id: slot.creative_id}));
      }
      const copy = el("div", "ad-slot__copy");
      copy.append(el("strong", "ad-slot__headline", slot.headline || ""));
      if (slot.body) copy.append(el("span", "ad-slot__body", slot.body));
      if (slot.advertiser) copy.append(el("span", "ad-slot__advertiser", slot.advertiser + (slot.preview ? " · " + slot.size : "")));
      card.append(copy);
      if (slot.cta) card.append(el("span", "ad-slot__cta", slot.cta));
      frame.append(card);
    }
    host.append(label, frame);
    host.hidden = false;
    if (!slot.preview) trackImpression(host, slot);
  }

  function trackImpression(host, slot) {
    if (!("IntersectionObserver" in window)) return;
    let timer = null;
    const observer = new IntersectionObserver((entries) => {
      const visible = entries.some((e) => e.isIntersecting && e.intersectionRatio >= 0.5);
      if (visible && !timer) {
        timer = setTimeout(() => {
          observer.disconnect();
          beacon({event: "impression", placement: slot.placement, creative_id: slot.creative_id});
        }, 1000);
      } else if (!visible && timer) {
        clearTimeout(timer); timer = null;
      }
    }, {threshold: [0, 0.5]});
    observer.observe(host);
  }

  // Columns of the lesson grid; the web version shows one banner per column
  // in the row between cards (Telegram Mini App keeps a single banner).
  function gridColumns() {
    const grid = document.getElementById("lessons");
    if (!grid || platform() !== "web") return 1;
    const tracks = getComputedStyle(grid).gridTemplateColumns.split(" ").filter(Boolean).length;
    return Math.max(1, Math.min(tracks || 1, 3));
  }

  // dashboard_between sits between lesson cards after the first full row:
  // one full-width banner, or one banner per grid cell when the server sent
  // a row. Never on top of a card or a learning control.
  function placeBetween(hosts) {
    const grid = document.getElementById("lessons");
    if (!grid) return;
    const row = hosts.length > 1;
    const move = () => {
      const cards = Array.from(grid.children).filter((n) => !hosts.includes(n));
      const columns = row ? hosts.length : 3;
      if (cards.length <= columns) return false;
      cards[columns - 1].after(...hosts);
      hosts.forEach((h) => {
        h.classList.remove("ad-slot--in-cell", "ad-slot--in-grid");
        h.classList.add(row ? "ad-slot--in-cell" : "ad-slot--in-grid");
      });
      return true;
    };
    if (move()) return;
    const observer = new MutationObserver(() => { if (move()) observer.disconnect(); });
    observer.observe(grid, {childList: true});
    setTimeout(() => observer.disconnect(), 15000);
  }

  function showConsentPrompt(prompt) {
    if (!prompt || document.getElementById("ads-consent-prompt")) return;
    const bar = el("div", "ads-consent-prompt");
    bar.id = "ads-consent-prompt";
    bar.setAttribute("role", "dialog");
    bar.setAttribute("aria-live", "polite");
    const text = el("div", "ads-consent-prompt__text");
    text.append(el("strong", "", prompt.title), el("span", "", prompt.text));
    const actions = el("div", "ads-consent-prompt__actions");
    [["granted", prompt.accept, "pill-btn"], ["denied", prompt.decline, "ghost-btn"]].forEach(([choice, label, cls]) => {
      const button = el("button", cls, label);
      button.type = "button";
      button.addEventListener("click", async () => {
        bar.remove();
        if (await saveConsent(choice).catch(() => false) && choice === "granted") load();
      });
      actions.append(button);
    });
    bar.append(text, actions);
    document.body.append(bar);
  }

  let loading = false;
  async function load() {
    if (!slots.length || loading) return;
    loading = true;
    try {
      const page = slots[0].dataset.adPage || "";
      const params = new URLSearchParams({
        page, device: device(), platform: platform(),
        placements: slots.map((s) => s.dataset.adPlacement).join(","),
        columns: String(gridColumns()),
      });
      const resp = await fetch("/api/ads/page?" + params.toString(), {credentials: "same-origin"});
      if (!resp.ok) return;
      const data = await resp.json();
      if (data.consent_prompt) showConsentPrompt(data.consent_prompt);
      const filled = new Map();
      (data.slots || []).forEach((s) => {
        if (!filled.has(s.placement)) filled.set(s.placement, []);
        filled.get(s.placement).push(s);
      });
      document.querySelectorAll("[data-ad-row-extra]").forEach((n) => n.remove());
      slots.forEach((host) => {
        const list = filled.get(host.dataset.adPlacement) || [];
        if (!list.length) { host.hidden = true; host.replaceChildren(); return; }
        if (list[0].placement === "dashboard_between") {
          // Extra cells for a banner row share the placement of the template slot.
          const hosts = [host].concat(list.slice(1).map(() => {
            const extra = el("aside", "ad-slot");
            extra.dataset.adRowExtra = "1";
            extra.hidden = true;
            return extra;
          }));
          placeBetween(hosts);
          list.forEach((slot, i) => renderSlot(hosts[i], slot));
          return;
        }
        renderSlot(host, list[0]);
      });
    } catch (e) {
      slots.forEach((host) => { host.hidden = true; });
    } finally {
      loading = false;
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", load);
  else load();
})();
