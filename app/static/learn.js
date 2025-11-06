/* app/static/learn.js
 * [v8.14] Показываем предложение в модалке для текущего языка (как в difficult.js):
 *         вычисляем nl/en/ru предложение и сохраняем в current._sent_for_modal при каждом рендере.
 * [v8.13] ⭐ Звезда "сложное слово": корректный начальный статус, клик добавляет/удаляет через API, синхронизация с чекбоксом.
 *         Фолбэк: если есть #difficultToggle (чекбокс), он синхронизирован со звездой.
 * [v8.12] Исправлен пул букв: клик скрывает букву (null-слот + перерисовка), Undo возвращает её. Кнопки с type="button".
 * [v8.11] Только одиночная генерация аудио.
 * [v8.10] Не перерисовываем карточку после генерации — ввод не сбивается.
 * [v8.9]  Анимация ▶, кнопки type="button".
 */
(function () {
  window.__LEARN_BOOTED__ = true;

  const $  = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));
  function escapeHtml(s){ return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
  async function apiGet(url){ const r = await window.apiFetch(url); return r.json(); }
  async function apiPost(url, body){
    const r = await window.apiFetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body||{})});
    return r.json();
  }
  function shuffle(a0){ const a=a0.slice(); for(let i=a.length-1;i>0;i--){ const j=(Math.random()*(i+1))|0; [a[i],a[j]]=[a[j],a[i]];} return a; }

  let root, wordBox, progress, answerSlots, lettersPool;
  let builder, builderControls, navRow;
  let btnClear, btnUndo, btnCheck, btnPrev, btnNext;
  let modal, modalClose, line1, line2, line3, btnNextWord, diffToggle;
  let langButtons;
  let starBtn; // [v8.13] кнопка-⭐ в модалке

  let LESSON=""; let ITEMS=[]; let index=0; let current=null;
  let currentLang="nl";
  let correct=""; let answer=[]; let pool=[];

  function pickAudioSrc(obj, lang){
    if (!obj) return "";
    if (lang==="nl") return obj.audio_nl||"";
    if (lang==="en") return obj.audio_en||"";
    if (lang==="ru") return obj.audio_ru||"";
    return "";
  }

  // --- одиночная генерация для текущего слова ---
  async function ensureAudioForCurrent(lang){
    if (!current || !window.AudioWorker?.ensureForWord) return;
    try{
      const up = await window.AudioWorker.ensureForWord(current, lang);
      if (up && typeof up==="object"){
        const i = ITEMS.findIndex(x=>x.id===current.id);
        if (i>=0) ITEMS[i]=up;
        current = up; // без ререндера
      }
    }catch(e){ console.warn("[Audio] ensureForWord failed", e); }
  }

  function blip(btn){
    if (!btn) return;
    btn.classList.remove("playing");
    void btn.offsetWidth;
    btn.classList.add("playing");
    setTimeout(()=>btn.classList.remove("playing"), 650);
  }

  async function playAudio(lang, btn){
    if (!current) return;
    let src = pickAudioSrc(current, lang);
    blip(btn);
    if (!src){
      await ensureAudioForCurrent(lang); // генерим ТОЛЬКО это слово
      src = pickAudioSrc(current, lang);
    }
    if (src){
      try{ new Audio(src).play().catch(()=>{}); }catch(e){ console.warn("play failed", e); }
    }
  }

  function setPracticeVisible(show){
    if (answerSlots)     answerSlots.style.display     = show ? "" : "none";
    if (lettersPool)     lettersPool.style.display     = show ? "" : "none";
    if (builderControls) builderControls.style.display = show ? "" : "none";
    if (navRow)          navRow.style.display          = "";
  }

  function setLanguage(langRaw){
    const norm = (langRaw==="" || langRaw==null) ? "all" : (langRaw || "nl");
    currentLang = norm;
    if (langButtons){
      langButtons.forEach(b=>{
        const dl = b.dataset.lang || "";
        const btnNorm = (dl==="" ? "all" : dl);
        b.classList.toggle("active", btnNorm===currentLang);
      });
    }
    if (ITEMS.length){
      renderCurrent();
      if (currentLang!=="all") ensureAudioForCurrent(currentLang);
    }
  }

  async function loadLesson(){
    if (!LESSON){ wordBox.textContent="Урок не выбран."; return; }
    wordBox.textContent="Загрузка...";
    try{
      const js = await apiGet("/api/lesson_words?lesson="+encodeURIComponent(LESSON));
      if (!js || js.ok===false){ wordBox.textContent="Ошибка загрузки слов."; return; }
      const items = js.items||[];
      if (!items.length){ wordBox.textContent="В этом уроке пока нет слов."; return; }
      ITEMS = items; index=0;

      try{ window.AudioWorker?.warmup?.(); }catch(e){}
      setLanguage(currentLang);
      renderCurrent();

      if (currentLang!=="all") ensureAudioForCurrent(currentLang);
    }catch(e){
      console.error(e); wordBox.textContent="Сеть недоступна.";
    }
  }

  function pickByLang(item){
    const nlW = item.translation_nl || item.nl_word || "";
    const enW = item.word_en        || item.en_word || "";
    const ruW = item.translation_ru || item.ru_word || "";
    const nlS = item.sentence_nl || "";
    const enS = item.sentence_en || "";
    const ruS = item.sentence_ru || "";

    if (currentLang === "all"){
      return { mode:"all", rows:[
        { head:`(nl) <b>${escapeHtml(nlW)}</b>`, sent:nlS, lang:"nl" },
        { head:`(en) <b>${escapeHtml(enW)}</b>`, sent:enS, lang:"en" },
        { head:`(ru) <b>${escapeHtml(ruW)}</b>`, sent:ruS, lang:"ru" },
      ]};
    }
    if (currentLang === "nl"){
      const correct = (nlW||"").trim() || (enW||ruW||"");
      return { mode:"one", correct, rows:[
        { head:`(en) <b>${escapeHtml(enW)}</b>`, sent:enS, lang:"en" },
        { head:`(ru) <b>${escapeHtml(ruW)}</b>`, sent:ruS, lang:"ru" },
      ]};
    }
    if (currentLang === "en"){
      const correct = (enW||"").trim() || (nlW||ruW||"");
      return { mode:"one", correct, rows:[
        { head:`(nl) <b>${escapeHtml(nlW)}</b>`, sent:nlS, lang:"nl" },
        { head:`(ru) <b>${escapeHtml(ruW)}</b>`, sent:ruS, lang:"ru" },
      ]};
    }
    const correct = (ruW||"").trim() || (nlW||enW||"");
    return { mode:"one", correct, rows:[
      { head:`(nl) <b>${escapeHtml(nlW)}</b>`, sent:nlS, lang:"nl" },
      { head:`(en) <b>${escapeHtml(enW)}</b>`, sent:enS, lang:"en" },
    ]};
  }

  function renderCurrent(){ current = ITEMS[index]; renderWordCard(); }

  function renderWordCard(){
    if (!current) return;
    const view = pickByLang(current);

    const makeRow = (r) => `
      <div class="row" style="align-items:center;gap:8px">
        <div>${r.head}</div>
        <button type="button" class="audio-btn mini" data-play="${r.lang}" title="▶">▶</button>
      </div>
      <div style="margin-bottom:8px">${escapeHtml(r.sent||"")}</div>
    `;

    // ---------- предложение для модалки ----------
    // [ДОБАВЛЕНО v8.14] вычисляем фразу для текущего языка (как в difficult.js)
    const nlS = current.sentence_nl || "";
    const enS = current.sentence_en || "";
    const ruS = current.sentence_ru || "";
    let sentForModal = "";
    // [ИЗМЕНЕНО v8.14] выбираем фразу под активный язык, затем фолбэк
    if (currentLang === "nl") sentForModal = nlS;
    else if (currentLang === "en") sentForModal = enS;
    else if (currentLang === "ru") sentForModal = ruS;
    if (!sentForModal) sentForModal = nlS || enS || ruS || "";

    if (view.mode === "all"){
      setPracticeVisible(false);
      wordBox.innerHTML = view.rows.map(makeRow).join("");
      progress.textContent = `${index + 1} / ${ITEMS.length}`;
      current._sent_for_modal = sentForModal; // [ДОБАВЛЕНО v8.14]
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
    current._sent_for_modal = sentForModal; // [ДОБАВЛЕНО v8.14]
  }

  function renderSlots(){
    const n = correct.length;
    const filled = answer.join("");
    answerSlots.innerHTML = Array.from({length:n})
      .map((_,i)=>`<div class="slot">${escapeHtml(filled[i]||"")}</div>`).join("");
  }

  // не рендерим кнопки для null-слотов — кликнутая буква исчезает
  function renderPool(){
    lettersPool.innerHTML = pool.map((ch,i)=>
      (ch==null) ? "" : `<button type="button" class="letter" data-i="${i}">${escapeHtml(ch)}</button>`
    ).join("");

    $$(".letter").forEach(btn=>{
      btn.addEventListener("click", ()=>{
        const i = Number(btn.dataset.i);
        const ch = pool[i];
        if (typeof ch !== "string") return;
        answer.push(ch);
        pool[i] = null;
        renderSlots();
        renderPool();
      });
    });
  }

  // ---------- ⭐ UI синхронизация ----------
  function updateDifficultUI(){
    const isDiff = Number(current?.difficult||0) === 1;
    const wid = String(current?.id||"");
    if (diffToggle){
      diffToggle.checked = isDiff;
      diffToggle.dataset.wordId = wid; // [v8.13] единый ключ
    }
    if (starBtn){
      starBtn.classList.toggle("on", isDiff);
      starBtn.setAttribute("aria-pressed", isDiff ? "true" : "false");
      starBtn.title = isDiff ? "Убрать из сложных" : "Добавить в сложные";
      starBtn.dataset.wordId = wid;
    }
  }

  async function setDifficultForCurrent(enabled){
    const wid = Number((starBtn?.dataset.wordId) || (diffToggle?.dataset.wordId) || "");
    if (!wid || isNaN(wid)) return;
    // Оптимистично обновим UI
    const prev = Number(current.difficult||0)===1;
    current.difficult = enabled ? 1 : 0;
    updateDifficultUI();
    try{
      const js = await apiPost("/api/difficult/user_set",{ word_id: wid, difficult: enabled ? 1 : 0 });
      if (!js || js.ok!==true) throw new Error("bad response");
    }catch(e){
      console.error(e);
      // откатим при ошибке
      current.difficult = prev ? 1 : 0;
      updateDifficultUI();
      alert("Не удалось сохранить статус «сложное слово». Проверьте соединение и попробуйте ещё раз.");
    }
  }

  function checkAnswer() {
    if (currentLang === "all") return;
    const user = answer.join("");
    const ok = (user === correct);

    // текст результата
    line1.textContent = ok ? "Правильно!" : "Неправильно!";
    line2.innerHTML = `Правильно: <b>${escapeHtml(correct)}</b>`;
    line3.textContent = current._sent_for_modal || ""; // [ИСПРАВЛЕНО v8.14] теперь заполнено при рендере
    modal.style.display = "block";

    // цветовая плашка
    if (ok) {
      line1.style.backgroundColor = "#16a34a";
      line1.style.border = "3px solid #15803d";
      line1.style.color = "#fff";
    } else {
      line1.style.backgroundColor = "#dc2626";
      line1.style.border = "3px solid #b91c1c";
      line1.style.color = "#fff";
    }
    line1.style.padding = "8px 12px";
    line1.style.borderRadius = "8px";
    line1.style.textAlign = "center";
    line1.style.fontWeight = "bold";

    // синхронизируем ⭐/чекбокс с текущим словом
    updateDifficultUI();
  }

  function closeModal(){ modal.style.display="none"; }
  function clearAnswer(){ answer=[]; renderWordCard(); }
  function undo(){
    if (!answer.length) return;
    const ch = answer.pop();
    const hole = pool.findIndex(x=>x===null);
    if (hole>=0) pool[hole]=ch; else pool.push(ch);
    renderSlots();
    renderPool();
  }
  function prevWord(){ index = (index - 1 + ITEMS.length) % ITEMS.length; renderCurrent(); }
  function nextWord(){ index = (index + 1) % ITEMS.length; renderCurrent(); }

  document.addEventListener("DOMContentLoaded", ()=>{
    root   = $("#learn-root");
    wordBox= $("#word-view");
    progress    = $("#progress");
    answerSlots = $("#answer-slots");
    lettersPool = $("#letters-pool");
    builder = $(".builder");
    builderControls = builder? builder.querySelector(".builder-controls") : null;
    navRow  = builder? builder.querySelector(".nav-row") : null;

    btnClear = $("#clear-btn");   btnUndo = $("#undo-btn");
    btnCheck = $("#check-btn");   btnPrev = $("#prev-btn"); btnNext = $("#next-btn");

    modal = $("#result-modal");   modalClose = $("#modal-close");
    line1 = $("#modal-line1");    line2 = $("#modal-line2"); line3 = $("#modal-line3");
    btnNextWord = $("#next-word-btn");
    diffToggle = $("#difficultToggle");      // чекбокс (если используется)
    starBtn    = $("#difficultStar");        // ⭐ (кнопка в правом верхнем углу модалки)

    langButtons = $$(".lang-switch .lang-btn");
    LESSON = (root && root.dataset.lesson) || window.LESSON_TITLE || "";

    btnClear?.addEventListener("click", clearAnswer);
    btnUndo?.addEventListener("click", undo);
    btnPrev?.addEventListener("click", prevWord);
    btnNext?.addEventListener("click", nextWord);
    btnCheck?.addEventListener("click", checkAnswer);
    modalClose?.addEventListener("click", closeModal);
    btnNextWord?.addEventListener("click", ()=>{ closeModal(); nextWord(); });

    // обработчики для ⭐ и чекбокса
    if (starBtn){
      starBtn.addEventListener("click", ()=>{
        const isOn = starBtn.classList.contains("on");
        setDifficultForCurrent(!isOn);
      });
    }
    if (diffToggle){
      diffToggle.addEventListener("change", (e)=> setDifficultForCurrent(!!e.target.checked));
    }

    langButtons.forEach(btn=> btn.addEventListener("click", ()=> setLanguage(btn.dataset.lang||"")));

    const btnNl = document.querySelector('.lang-switch .lang-btn[data-lang="nl"]');
    if (btnNl) btnNl.classList.add("active");
    currentLang="nl";

    loadLesson();
  });
})();
