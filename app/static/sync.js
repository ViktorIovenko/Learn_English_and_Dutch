(() => {
  const IDB = window.LocalDB || null;
  const IDB_PREFIX = window.IDB_KEY_PREFIX || (window.USER_ID ? `uid:${window.USER_ID}:` : "uid:anon:");
  const SYNC_URL = "/api/progress/sync";
  const DELTA_URL = "/api/sync/updates";
  const META_STORE = "meta/state";
  const LAST_SYNC_KEY = IDB_PREFIX + "last_sync";
  const LESSONS_KEY = IDB_PREFIX + "list";
  const WORDS_KEY_PREFIX = IDB_PREFIX + "lesson:";
  const BASE_DELAY_MS = 5000;
  const MAX_DELAY_MS = 60000;

  let syncInFlight = false;
  let retryTimer = null;
  let retryDelay = BASE_DELAY_MS;

  function scheduleRetry() {
    if (retryTimer) return;
    retryTimer = setTimeout(() => {
      retryTimer = null;
      syncAll();
    }, retryDelay);
    retryDelay = Math.min(retryDelay * 2, MAX_DELAY_MS);
  }

  function isKeyForUser(key) {
    return String(key || "").startsWith(IDB_PREFIX);
  }

  async function readOutboxEntries() {
    if (!IDB?.entries) return [];
    const items = await IDB.entries("outbox");
    return (items || []).filter((item) => isKeyForUser(item.key));
  }

  async function clearOutboxKeys(keys) {
    if (!keys || !keys.length) return;
    if (IDB?.delMany) {
      await IDB.delMany("outbox", keys);
      return;
    }
    await Promise.all(keys.map((key) => IDB.del("outbox", key)));
  }

  async function postBatch(events) {
    const body = JSON.stringify({ events });
    if (window.apiFetch) {
      return window.apiFetch(SYNC_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body
      });
    }
    return fetch(SYNC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body
    });
  }

  async function pushOutboxOnce() {
    const entries = await readOutboxEntries();
    if (!entries || entries.length === 0) return;
    const payload = entries.map((item) => item.value);
    const resp = await postBatch(payload);
    if (!resp || !resp.ok) throw new Error("bad response");
    let js = null;
    try { js = await resp.json(); } catch (_) {}
    if (js && js.ok === false) throw new Error("server rejected");
    const keys = entries.map((item) => item.key);
    await clearOutboxKeys(keys);
  }

  async function getLastSync() {
    if (!IDB) return 0;
    try {
      const val = await IDB.get(META_STORE, LAST_SYNC_KEY);
      return Number(val) || 0;
    } catch (_) {
      return 0;
    }
  }

  async function setLastSync(ts) {
    if (!IDB) return;
    try { await IDB.set(META_STORE, ts, LAST_SYNC_KEY); } catch (_) {}
  }

  function sortLessons(items) {
    items.sort((a, b) => {
      const ah = Number(a.hidden || 0), bh = Number(b.hidden || 0);
      if (ah !== bh) return ah - bh;
      const ai = Number(a.lesson_index || 0), bi = Number(b.lesson_index || 0);
      if (ai !== bi) return ai - bi;
      return String(a.lesson || "").localeCompare(String(b.lesson || ""), "ru");
    });
  }

  function sortWords(items) {
    items.sort((a, b) => {
      return String(a.number || "").localeCompare(String(b.number || ""), "ru", { numeric: true });
    });
  }

  async function applyWordDelta(words) {
    if (!words || !words.length) return;
    const byLesson = new Map();
    words.forEach((w) => {
      const lesson = String(w.lesson || "");
      if (!lesson) return;
      const list = byLesson.get(lesson) || [];
      list.push(w);
      byLesson.set(lesson, list);
    });

    for (const [lesson, updates] of byLesson.entries()) {
      const key = WORDS_KEY_PREFIX + lesson;
      let existing = await IDB.get("words", key);
      if (!Array.isArray(existing)) existing = [];
      const byId = new Map(existing.map((w) => [String(w.id || ""), w]));
      updates.forEach((u) => {
        const id = String(u.id || "");
        if (!id) return;
        const target = byId.get(id);
        if (target) Object.assign(target, u);
        else { existing.push(u); byId.set(id, u); }
      });
      sortWords(existing);
      await IDB.set("words", existing, key);
    }
  }

  async function applyLessonsDelta(lessons, userLessons) {
    if (!lessons && !userLessons) return;
    let list = await IDB.get("lessons", LESSONS_KEY);
    if (!Array.isArray(list)) list = [];
    const byLesson = new Map(list.map((l) => [String(l.lesson || ""), l]));

    (lessons || []).forEach((l) => {
      const key = String(l.lesson || "");
      if (!key) return;
      const target = byLesson.get(key);
      if (target) Object.assign(target, l);
      else { list.push(l); byLesson.set(key, l); }
    });

    (userLessons || []).forEach((u) => {
      const key = String(u.lesson || "");
      const target = byLesson.get(key);
      if (target) target.hidden = Number(u.hidden || 0);
    });

    if (list.length) {
      sortLessons(list);
      await IDB.set("lessons", list, LESSONS_KEY);
    }
  }

  async function syncUpdatesOnce() {
    const since = await getLastSync();
    const url = `${DELTA_URL}?since=${encodeURIComponent(String(since))}`;
    const resp = window.apiFetch ? await window.apiFetch(url) : await fetch(url);
    if (!resp || !resp.ok) throw new Error("bad delta response");
    const js = await resp.json();
    if (!js || js.ok === false) throw new Error("delta rejected");
    await applyWordDelta(js.words || []);
    await applyLessonsDelta(js.lessons || [], js.user_lessons || []);
    const ts = Number(js.server_ts) || Date.now();
    await setLastSync(ts);
  }

  async function syncAll() {
    if (!IDB || syncInFlight) return;
    if (typeof navigator !== "undefined" && navigator.onLine === false) return;
    syncInFlight = true;
    try {
      await pushOutboxOnce();
      await syncUpdatesOnce();
      retryDelay = BASE_DELAY_MS;
    } catch (_) {
      scheduleRetry();
    } finally {
      syncInFlight = false;
    }
  }

  function kickSync() {
    syncAll().catch(() => {});
  }

  window.addEventListener("online", () => kickSync());
  if (document.readyState === "complete") {
    kickSync();
  } else {
    window.addEventListener("load", () => kickSync());
  }
})();
