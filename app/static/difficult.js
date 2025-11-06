/* app/static/difficult.js
 * [v8.7]
 * - ▶-кнопки напротив каждого отображаемого слова + анимация "playing"
 * - Генерация аудио только для текущего слова/языка через AudioWorker.ensureForWord
 * - Кнопки type="button" (не сбрасывают ввод)
 * - Интерфейс и логика максимально совпадают с learn.js
 * - [ИЗМЕНЕНО v8.6] В модальном окне показываем предложение для текущего языка
 * - [ИЗМЕНЕНО v8.7] Кнопка-литера исчезает из пула после клика, возвращается через Undo
 * - [ИЗМЕНЕНО v8.7] Цветная обводка/заливка результата (зелёный/красный), белый текст
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
  // стартовый язык — "nl"
  let currentLang = "nl";
  let correct = "";
  let answer  = [];
  let pool    = [];

  // ---------------- Аудио (новое) ----------------
  function pickAudioSrc(obj, lang){
    if (!obj) return "";
    if (lang==="nl") return obj.audio_nl || obj.nl_audio || "";
    if (lang==="en") return obj.audio_en || obj.en_audio || "";
    if (lang==="ru") return obj.audio_ru || obj.ru_audio || "";
    return "";
  }
  function blip(btn){
    if (!btn) return;
    btn.classList.remove("playing"); // перезапуск анимации
    void btn.offsetWidth;
    btn.classList.add("playing");
    setTimeout(()=>btn.classList.remove("playing"), 650);
  }
  // генерация ТОЛЬКО для текущего слова и выбранного языка
  async function ensureAudioForCurrent(lang){
    if (!current || !window.AudioWorker?.ensureForWord) return;
    try{
      const up = await window.AudioWorker.ensureForWord(current, lang);
      if (up && typeof up==="object"){
        const i = ITEMS.findIndex(x=>String(x.id)===String(current.id));
        if (i>=0) ITEMS[i]=up;
        current = up; // без полного ререндера (не сбиваем ввод)
      }
    }catch(e){ console.warn("[Audio] ensureForWord failed", e); }
  }
  async function playAudio(lang, btn){
    if (!current) return;
    let src = pickAudioSrc(current, lang);
    blip(btn);
    if (!src){
      await ensureAudioForCurrent(lang);
      src = pickAudioSrc(current, lang);
    }
    if (src){
      try{ new Audio(src).play().catch(()=>{}); }catch(e){ console.warn("play failed", e); }
    }
  }

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

      try{ window.AudioWorker?.warmup?.(); }catch(e){}

      setLanguage(currentLang);
      renderCurrent();

      // при входе генерим только для активного языка, если он не "all"
      if (currentLang!=="all") ensureAudioForCurrent(currentLang);
    } catch (e) {
      console.error(e);
      wordBox.textContent = "Не удалось загрузить список. Проверьте сеть.";
      setPracticeVisible(false);
    }
  }

  // ---------------- Язык ----------------
  function setLanguage(langRaw) {
    const norm = (langRaw === "" || langRaw == null) ? "all" : (langRaw || "nl");
    currentLang = norm;
    langButtons.forEach(b => {
      const dl = b.dataset.lang || "";
      const btnNorm = (dl === "" ? "all" : dl);
      b.classList.toggle("active", btnNorm === currentLang);
    });
    if (ITEMS.length){
      renderCurrent();
      if (currentLang!=="all") ensureAudioForCurrent(currentLang);
    }
  }

  // ---------------- Подготовка данных для вью ----------------
  function pickByLang(item) {
    const nlW = item.translation_nl || item.nl_word || "";
    const enW = item.word_en        || item.en_word || "";
    const ruW = item.translation_ru || item.ru_word || "";

    const nlS = item.sentence_nl || "";
    const enS = item.sentence_en || "";
    const ruS = item.sentence_ru || "";

    if (currentLang === "all") {
      return {
        mode: "all",
        rows: [
          { head:`(nl) <b>${escapeHtml(nlW)}</b>`, sent:nlS, lang:"nl" },
          { head:`(en) <b>${escapeHtml(enW)}</b>`, sent:enS, lang:"en" },
          { head:`(ru) <b>${escapeHtml(ruW)}</b>`, sent:ruS, lang:"ru" },
        ]
      };
    }

    if (currentLang === "nl") {
      const correct = (nlW || "").trim() || (enW || ruW || "");
      return {
        mode: "one",
        correct,
        rows: [
          { head:`(en) <b>${escapeHtml(enW)}</b>`, sent:enS, lang:"en" },
          { head:`(ru) <b>${escapeHtml(ruW)}</b>`, sent:ruS, lang:"ru" },
        ]
      };
    }
    if (currentLang === "en") {
      const correct = (enW || "").trim() || (nlW || ruW || "");
      return {
        mode: "one",
        correct,
        rows: [
          { head:`(nl) <b>${escapeHtml(nlW)}</b>`, sent:nlS, lang:"nl" },
          { head:`(ru) <b>${escapeHtml(ruW)}</b>`, sent:ruS, lang:"ru" },
        ]
      };
    }
    // ru
    const correct = (ruW || "").trim() || (nlW || enW || "");
    return {
      mode: "one",
      correct,
      rows: [
        { head:`(nl) <b>${escapeHtml(nlW)}</b>`, sent:nlS, lang:"nl" },
        { head:`(en) <b>${escapeHtml(enW)}</b>`, sent:enS, lang:"en" },
      ]
    };
  }

  // ---------------- Рендер ----------------
  function renderCurrent() {
    current = ITEMS[index];
    renderWordCard();
  }

  function renderWordCard() {
    if (!current) return;
    const view = pickByLang(current);

    const makeRow = (r) => `
      <div class="row" style="align-items:center;gap:8px">
        <div>${r.head}</div>
        <button type="button" class="audio-btn mini" data-play="${r.lang}" title="▶">▶</button>
      </div>
      <div style="margin-bottom:8px">${escapeHtml(r.sent||"")}</div>
    `;

    // [ИЗМЕНЕНО v8.6] вычисляем предложение для модалки в зависимости от текущего языка
    const nlS = current.sentence_nl || "";
    const enS = current.sentence_en || "";
    const ruS = current.sentence_ru || "";
    let sentForModal = "";
    if (currentLang === "nl") sentForModal = nlS;
    else if (currentLang === "en") sentForModal = enS;
    else if (currentLang === "ru") sentForModal = ruS;
    // fallback, если у текущего языка нет предложения
    if (!sentForModal) sentForModal = nlS || enS || ruS || "";

    if (view.mode === "all") {
      setPracticeVisible(false);
      wordBox.innerHTML = view.rows.map(makeRow).join("");
      progress.textContent = `${index + 1} / ${ITEMS.length}`;
      // [ИЗМЕНЕНО v8.6] сохраняем предложение для модалки (на случай будущего использования)
      current._sent_for_modal = sentForModal;

      $$("#word-view .audio-btn").forEach(btn=>{
        btn.addEventListener("click", ()=> playAudio(btn.dataset.play||"nl", btn));
      });
      return;
    }

    setPracticeVisible(true);
    correct = (view.correct || "—").trim();

    wordBox.innerHTML = view.rows.map(makeRow).join("");
    $$("#word-view .audio-btn").forEach(btn=>{
      btn.addEventListener("click", ()=> playAudio(btn.dataset.play||"nl", btn));
    });

    pool = shuffle(correct.split(""));
    answer = [];
    renderSlots();
    renderPool();
    progress.textContent = `${index + 1} / ${ITEMS.length}`;

    // [ИЗМЕНЕНО v8.6] сохраняем предложение для модалки
    current._sent_for_modal = sentForModal;
  }

  function renderSlots() {
    const n = correct.length;
    const filled = answer.join("");
    answerSlots.innerHTML = Array.from({ length: n })
      .map((_, i) => `<div class="slot">${escapeHtml(filled[i] || "")}</div>`).join("");
  }

  // [ИЗМЕНЕНО v8.7] — не рендерим кнопки для null-слотов,
  // чтобы кликнутая буква исчезала из пула. Индекс исходного слота сохраняем.
  function renderPool() {
    lettersPool.innerHTML = pool.map((ch, i) =>
      (ch == null)
        ? "" 
        : `<button type="button" class="letter" data-i="${i}">${escapeHtml(ch)}</button>`
    ).join("");

    $$(".letter").forEach(btn => {
      btn.addEventListener("click", () => {
        const i = Number(btn.dataset.i);
        const ch = pool[i];
        if (typeof ch !== "string") return;
        answer.push(ch);
        pool[i] = null;                 // помечаем слот пустым
        renderSlots();                  // перерисовали слоты
        renderPool();                   // [ИЗМЕНЕНО v8.7] перерисовали пул -> кнопка исчезла
      });
    });
  }

  // ---------------- Проверка и статус ----------------
  function checkAnswer() {
    if (currentLang === "all") return;
    const user = answer.join("");
    const ok = (user === correct);

    // текст результата
    line1.textContent = ok ? "Правильно!" : "Неправильно!";
    line2.innerHTML = `Правильно: <b>${escapeHtml(correct)}</b>`;
    line3.textContent = current._sent_for_modal || "";
    diffToggle.checked = Number(current.difficult || 1) === 1;
    diffToggle.dataset.id = String(current.id);
    modal.style.display = "block";

    // [ИЗМЕНЕНО v8.7] визуальное оформление результата (зелёный/красный)
    if (ok) {
      line1.style.backgroundColor = "#16a34a";   // зелёная заливка
      line1.style.border = "3px solid #15803d";  // обводка потемнее
      line1.style.color = "#fff";                // белый текст
    } else {
      line1.style.backgroundColor = "#dc2626";   // красная заливка
      line1.style.border = "3px solid #b91c1c";  // обводка потемнее
      line1.style.color = "#fff";                // белый текст
    }
    line1.style.padding = "8px 12px";
    line1.style.borderRadius = "8px";
    line1.style.textAlign = "center";
    line1.style.fontWeight = "bold";
  }
  function closeModal(){ modal.style.display = "none"; }

  async function setPersonalDifficult(enabled){
    const id = diffToggle.dataset.id || "";
    try {
      const wid = Number(id);
      if (!wid || isNaN(wid)) throw new Error("bad id");
      const js = await apiPost("/api/difficult/user_set", {
        word_id: wid,
        difficult: enabled ? 1 : 0
      });
      if (!js || js.ok !== true) throw new Error("bad response");

      current.difficult = enabled ? 1 : 0;
      if (!enabled) {
        // убираем из списка и показываем следующее
        ITEMS = ITEMS.filter(x => String(x.id) !== String(id));
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
    renderSlots();
    renderPool();   // вернули букву — пул перерисован
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
  langButtons.forEach(btn => btn.addEventListener("click", () => setLanguage(btn.dataset.lang || "")));

  // Визуально активируем Dutch на старте
  const btnNl = document.querySelector('.lang-switch .lang-btn[data-lang="nl"]');
  if (btnNl) btnNl.classList.add("active");
  currentLang = "nl";

  // Старт
  loadDifficult();
})();
