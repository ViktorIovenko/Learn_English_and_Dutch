/* app/static/difficult.js
 * [v8.4] Интерфейс как в learn:
 *  - загрузка только персональных слов: /api/difficult_words_user
 *  - язык по умолчанию "nl" (Dutch)
 *  - режим "Все" показывает nl/en/ru + аудио и скрывает поле ввода/буквы/проверку
 *  - поддержка пользовательских слов (id вида "c_<num>")
 *  - при снятии "В сложные" слово удаляется из тренировки
 */

(function () {
  // ---------------- Утилиты ----------------
  const $  = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }
  async function apiGet(url) {
    const r = await (window.apiFetch ? window.apiFetch(url) : fetch(url));
    return r.json();
  }
  async function apiPost(url, body) {
    const r = await (window.apiFetch ? window.apiFetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {})
    }) : fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {})
    }));
    return r.json();
  }
  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = (Math.random() * (i + 1)) | 0;
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }
  function isCustomId(id) { return String(id).startsWith("c_"); }
  function customNum(id)  { return Number(String(id).replace(/^c_/, "")); }

  // ---------------- DOM ----------------
  const wordBox      = $("#word-view");
  const progress     = $("#progress");
  const answerSlots  = $("#answer-slots");
  const lettersPool  = $("#letters-pool");

  const builder      = $(".builder");
  const builderControls = builder ? builder.querySelector(".builder-controls") : null;
  const navRow       = builder ? builder.querySelector(".nav-row") : null;

  const btnClear     = $("#clear-btn");
  const btnUndo      = $("#undo-btn");
  const btnCheck     = $("#check-btn");
  const btnPrev      = $("#prev-btn");
  const btnNext      = $("#next-btn");

  const modal        = $("#result-modal");
  const modalClose   = $("#modal-close");
  const line1        = $("#modal-line1");
  const line2        = $("#modal-line2");
  const line3        = $("#modal-line3");
  const btnNextWord  = $("#next-word-btn");
  const diffToggle   = $("#difficultToggle");

  const langButtons  = $$(".lang-switch .lang-btn");

  // ---------------- Состояние ----------------
  let ITEMS   = [];   // персональные «сложные» для пользователя
  let index   = 0;
  let current = null;

  // [ИЗМЕНЕНО v8.4] Стартовый язык — "nl"
  let currentLang = "nl";

  let correct = "";
  let answer  = [];
  let pool    = [];

  function setPracticeVisible(show) {
    if (answerSlots)      answerSlots.style.display      = show ? "" : "none";
    if (lettersPool)      lettersPool.style.display      = show ? "" : "none";
    if (builderControls)  builderControls.style.display  = show ? "" : "none";
    if (navRow)           navRow.style.display           = "";
  }

  // ---------------- Загрузка ----------------
  async function loadDifficult() {
    wordBox.textContent = "Загрузка...";
    try {
      const js = await apiGet("/api/difficult_words_user");
      const items = (js && js.items) ? js.items : [];
      if (!items.length) {
        wordBox.textContent = "У вас пока нет отмеченных сложных слов.";
        progress.textContent = "0 / 0";
        setPracticeVisible(false);
        return;
      }
      ITEMS = items;
      index = 0;

      // синхронизируем выбранный язык и рендерим
      setLanguage(currentLang);
      renderCurrent();
    } catch (e) {
      console.error(e);
      wordBox.textContent = "Не удалось загрузить список. Проверьте сеть.";
      setPracticeVisible(false);
    }
  }

  // ---------------- Язык ----------------
  function setLanguage(langRaw) {
    // "" → "all", иначе конкретный язык; по умолчанию "nl"
    const norm = (langRaw === "" || langRaw == null) ? "all" : (langRaw || "nl");
    currentLang = norm;
    langButtons.forEach(b => {
      const dl = b.dataset.lang || "";
      const btnNorm = (dl === "" ? "all" : dl);
      b.classList.toggle("active", btnNorm === currentLang);
    });
    if (ITEMS.length) renderCurrent();
  }

  // ---------------- Подготовка вью ----------------
  function pickByLang(item) {
    const nlW = item.translation_nl || item.nl_word || "";
    const enW = item.word_en        || item.en_word || "";
    const ruW = item.translation_ru || item.ru_word || "";

    const nlS = item.sentence_nl || "";
    const enS = item.sentence_en || "";
    const ruS = item.sentence_ru || "";

    const nlA = item.nl_audio || item.audio_nl || "";
    const enA = item.en_audio || item.audio_en || "";
    const ruA = item.ru_audio || item.audio_ru || "";

    if (currentLang === "all") {
      return {
        mode: "all",
        html: `
          <div>(nl) <b>${escapeHtml(nlW)}</b></div>
          <div style="margin-bottom:4px">${escapeHtml(nlS)}</div>
          <div>(en) <b>${escapeHtml(enW)}</b></div>
          <div style="margin-bottom:4px">${escapeHtml(enS)}</div>
          <div>(ru) <b>${escapeHtml(ruW)}</b></div>
          <div style="margin-bottom:8px">${escapeHtml(ruS)}</div>
          ${nlA ? `<audio controls src="${nlA}" style="margin:4px 0"></audio>` : ``}
          ${enA ? `<audio controls src="${enA}" style="margin:4px 0"></audio>` : ``}
          ${ruA ? `<audio controls src="${ruA}" style="margin:4px 0"></audio>` : ``}
        `,
        sent: ""
      };
    }

    let nextCorrect = "", showA = "", showB = "", sent = "", audioSrc = "";
    if (currentLang === "nl") {
      nextCorrect = (nlW || "").trim() || (enW || ruW || "");
      showA       = `(en) <b>${escapeHtml(enW)}</b>\n${escapeHtml(enS)}`;
      showB       = `(ru) <b>${escapeHtml(ruW)}</b>\n${escapeHtml(ruS)}`;
      sent        = nlS;  audioSrc = nlA || "";
    } else if (currentLang === "en") {
      nextCorrect = (enW || "").trim() || (nlW || ruW || "");
      showA       = `(nl) <b>${escapeHtml(nlW)}</b>\n${escapeHtml(nlS)}`;
      showB       = `(ru) <b>${escapeHtml(ruW)}</b>\n${escapeHtml(ruS)}`;
      sent        = enS;  audioSrc = enA || "";
    } else {
      nextCorrect = (ruW || "").trim() || (nlW || enW || "");
      showA       = `(nl) <b>${escapeHtml(nlW)}</b>\n${escapeHtml(nlS)}`;
      showB       = `(en) <b>${escapeHtml(enW)}</b>\n${escapeHtml(enS)}`;
      sent        = ruS;  audioSrc = ruA || "";
    }
    if (!nextCorrect) nextCorrect = (nlW || enW || ruW || "—").trim();
    return { mode: "one", correct: nextCorrect, showA, showB, sent, audioSrc };
  }

  // ---------------- Рендер ----------------
  function renderCurrent() {
    current = ITEMS[index];
    renderWordCard();
  }

  function renderWordCard() {
    if (!current) return;
    const view = pickByLang(current);

    if (view.mode === "all") {
      setPracticeVisible(false);
      wordBox.innerHTML = view.html;
      progress.textContent = `${index + 1} / ${ITEMS.length}`;
      current._sent_for_modal = "";
      return;
    }

    setPracticeVisible(true);

    correct = view.correct;
    const [aHead, aBody] = (view.showA || "").split("\n");
    const [bHead, bBody] = (view.showB || "").split("\n");

    wordBox.innerHTML = `
      <div>${aHead || ""}</div>
      <div style="margin-bottom:4px">${aBody || ""}</div>
      <div>${bHead || ""}</div>
      <div style="margin-bottom:8px">${bBody || ""}</div>
      ${view.audioSrc ? `<audio controls src="${view.audioSrc}" style="margin:6px 0"></audio>` : ``}
    `;
    current._sent_for_modal = (view.sent || "").trim();

    pool = shuffle(correct.split(""));
    answer = [];
    renderSlots();
    renderPool();

    progress.textContent = `${index + 1} / ${ITEMS.length}`;
  }

  function renderSlots() {
    const n = correct.length;
    const filled = answer.join("");
    answerSlots.innerHTML = Array.from({ length: n })
      .map((_, i) => `<div class="slot">${escapeHtml(filled[i] || "")}</div>`).join("");
  }
  function renderPool() {
    lettersPool.innerHTML = pool.map((ch, i) =>
      `<button class="letter" data-i="${i}">${escapeHtml(ch)}</button>`).join("");
    $$(".letter").forEach(btn => {
      btn.addEventListener("click", () => {
        const i = Number(btn.dataset.i);
        const ch = pool[i];
        if (typeof ch !== "string") return;
        answer.push(ch);
        pool[i] = null;
        btn.disabled = true;
        btn.classList.add("used");
        renderSlots();
      });
    });
  }

  // ---------------- Проверка и статус ----------------
  function checkAnswer() {
    if (currentLang === "all") return;
    const user = answer.join("");
    const ok = (user === correct);
    line1.textContent = ok ? "Правильно!" : "Неправильно!";
    line2.innerHTML = `Правильно: <b>${escapeHtml(correct)}</b>`;
    line3.textContent = current._sent_for_modal || "";

    diffToggle.checked = Number(current.difficult || 1) === 1;
    diffToggle.dataset.id = String(current.id);

    modal.style.display = "block";
  }
  function closeModal(){ modal.style.display = "none"; }

  async function setPersonalDifficult(enabled){
    const id = diffToggle.dataset.id || "";
    try {
      if (isCustomId(id)) {
        const js = await apiPost("/api/custom_words/set_difficult", {
          id: customNum(id),
          difficult: enabled ? 1 : 0
        });
        if (!js || js.ok !== true) throw new Error("bad response");
      } else {
        const wid = Number(id);
        if (!wid || isNaN(wid)) throw new Error("bad id");
        const js = await apiPost("/api/difficult/user_set", {
          word_id: wid,
          difficult: enabled ? 1 : 0
        });
        if (!js || js.ok !== true) throw new Error("bad response");
      }
      current.difficult = enabled ? 1 : 0;

      // Если сняли флаг — убираем слово из списка и рендерим следующее
      if (!enabled) {
        const idStr = String(id);
        ITEMS = ITEMS.filter(x => String(x.id) !== idStr);
        if (!ITEMS.length) {
          closeModal();
          wordBox.textContent = "Все слова изучены. Список пуст.";
          progress.textContent = "0 / 0";
          answerSlots.innerHTML = "";
          lettersPool.innerHTML = "";
          setPracticeVisible(false);
          return;
        }
        index = index % ITEMS.length;
        closeModal();
        renderCurrent();
      }
    } catch (e) {
      console.error(e);
      diffToggle.checked = !enabled;
      alert("Не удалось сохранить статус «сложное слово». Повторите позже.");
    }
  }

  // ---------------- Навигация/действия ----------------
  function clearAnswer(){ answer = []; renderWordCard(); }
  function undo(){
    if (!answer.length) return;
    const ch = answer.pop();
    const hole = pool.findIndex(x => x === null);
    if (hole >= 0) pool[hole] = ch; else pool.push(ch);
    renderSlots(); renderPool();
  }
  function prevWord(){ index = (index - 1 + ITEMS.length) % ITEMS.length; renderCurrent(); }
  function nextWord(){ index = (index + 1) % ITEMS.length; renderCurrent(); }

  // ---------------- Слушатели ----------------
  btnClear.addEventListener("click", clearAnswer);
  btnUndo.addEventListener("click", undo);
  btnPrev.addEventListener("click", prevWord);
  btnNext.addEventListener("click", nextWord);
  btnCheck.addEventListener("click", checkAnswer);

  modalClose.addEventListener("click", closeModal);
  btnNextWord.addEventListener("click", () => { closeModal(); nextWord(); });
  diffToggle.addEventListener("change", (e) => setPersonalDifficult(!!e.target.checked));

  langButtons.forEach(btn => {
    btn.addEventListener("click", () => setLanguage(btn.dataset.lang || ""));
  });

  // [ДОБАВЛЕНО v8.4] Визуально активируем Dutch на старте
  const btnNl = document.querySelector('.lang-switch .lang-btn[data-lang="nl"]');
  if (btnNl) btnNl.classList.add("active");
  currentLang = "nl";

  // Старт
  loadDifficult();
})();
