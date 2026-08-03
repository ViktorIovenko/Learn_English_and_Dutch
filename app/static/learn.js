/* app/static/learn.js
 * [v8.24] Кнопка ▶ вставляется прямо в строку «Правильно: …» (без текста-подсказки).
 * [v8.23] Аудио в модалке результата: кнопка ▶ воспроизводит правильное слово на текущем языке.
 * [v8.22] ВОЗВРАТ: setDifficultForCurrent() + синхронизация UI звезды/чекбокса.
 * [v8.21] Анти-дубль перехода advanceToNextOnce().
 * [v8.20] Клик по заполненной ячейке ответа возвращает букву в пул.
 * [v8.19] Фикс двойного nextWord().
 * [v8.18] Фейерверк на последнем слове.
 */
(function () {
  window.__LEARN_BOOTED__ = true;
  const $  = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));
  const tr = (key, params) => (window.I18N && window.I18N.t) ? window.I18N.t(key, params) : key;
  function escapeHtml(s){ return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
  function renderSentence(s){ return escapeHtml(s).replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>"); }
  async function apiGet(url){ const r = await window.apiFetch(url); return r.json(); }
  async function apiPost(url, body){
    const r = await window.apiFetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body||{})});
    return r.json();
  }
  const IDB = window.LocalDB || null;
  const IDB_PREFIX = window.IDB_KEY_PREFIX || (window.USER_ID ? `uid:${window.USER_ID}:` : "uid:anon:");
  const LESSONS_KEY = IDB_PREFIX + "list";
  const WORDS_KEY_PREFIX = IDB_PREFIX + "lesson:";
  let lessonsCache = null;

  function isNonEmptyArray(val){
    return Array.isArray(val) && val.length > 0;
  }
  function itemsSig(items){
    if (!Array.isArray(items) || !items.length) return "";
    return items.map((i) => Object.keys(i)
      .filter(key => key === "id" || key === "number" || /^(?:[a-z]{2}_(?:word|sentence)|(?:word|sentence)_[a-z]{2})$/.test(key))
      .sort()
      .map(key => `${key}:${i[key] ?? ""}`)
      .join("|")
    ).join("||");
  }
  async function idbGet(store, key){
    if (!IDB) return null;
    try { return await IDB.get(store, key); } catch (_) { return null; }
  }
  async function idbSet(store, key, value){
    if (!IDB) return false;
    try { await IDB.set(store, value, key); return true; } catch (_) { return false; }
  }
  async function readLessonWordsFromIdb(lesson){
    if (!lesson) return null;
    const key = WORDS_KEY_PREFIX + lesson;
    const cached = await idbGet("words", key);
    return Array.isArray(cached) ? cached : null;
  }
  async function writeLessonWordsToIdb(lesson, items){
    if (!lesson || !Array.isArray(items)) return;
    const key = WORDS_KEY_PREFIX + lesson;
    await idbSet("words", key, items);
  }
  async function readLessonsFromIdb(){
    if (Array.isArray(lessonsCache)) return lessonsCache;
    const cached = await idbGet("lessons", LESSONS_KEY);
    if (Array.isArray(cached)) { lessonsCache = cached; return cached; }
    return null;
  }
  async function writeLessonsToIdb(lessons){
    if (!Array.isArray(lessons)) return;
    lessonsCache = lessons;
    await idbSet("lessons", LESSONS_KEY, lessons);
  }
  async function updateLessonHiddenCache(lesson, hidden){
    if (!lesson) return;
    const lessons = await readLessonsFromIdb();
    if (!isNonEmptyArray(lessons)) return;
    const needle = String(lesson || "");
    const found = lessons.find((x)=> String(x.lesson || x.lesson_title || "") === needle);
    if (found) found.hidden = hidden;
    await writeLessonsToIdb(lessons);
  }
  const PROGRESS_KEY_PREFIX = IDB_PREFIX + "lesson:";
  let lastProgressSig = null;
  let progressSigLoaded = false;

  function countPassed(){
    let n = 0;
    for (const w of ITEMS) {
      if (w && w._passed === true) n += 1;
    }
    return n;
  }
  function progressSig(p){
    return [
      p.kind || "",
      p.lesson || "",
      String(p.index ?? ""),
      String(p.total ?? ""),
      String(p.word_id ?? ""),
      String(p.passed ?? ""),
      p.lang || "",
      p.reason || ""
    ].join("|");
  }
  function buildProgressPayload(reason){
    if (!LESSON) return null;
    const total = Array.isArray(ITEMS) ? ITEMS.length : 0;
    return {
      kind: "learn",
      lesson: LESSON,
      index: total ? index : 0,
      total,
      word_id: current?.id ?? null,
      passed: total ? countPassed() : 0,
      lang: currentLang,
      reason: reason || "",
      tz_offset: new Date().getTimezoneOffset(),
      ts: Date.now()
    };
  }
  function makeOutboxKey(ts){
    return IDB_PREFIX + `progress:${ts}:${Math.random().toString(36).slice(2,8)}`;
  }
  async function ensureProgressSig(key){
    if (progressSigLoaded) return;
    progressSigLoaded = true;
    const existing = await idbGet("progress", key);
    if (existing) lastProgressSig = progressSig(existing);
  }
  async function saveProgress(reason){
    if (!IDB) return;
    const payload = buildProgressPayload(reason);
    if (!payload) return;
    const key = PROGRESS_KEY_PREFIX + LESSON;
    await ensureProgressSig(key);
    const sig = progressSig(payload);
    if (sig === lastProgressSig) return;
    lastProgressSig = sig;
    await idbSet("progress", key, payload);
    const event = { type: "progress", scope: "learn", state: payload, ts: payload.ts };
    await idbSet("outbox", makeOutboxKey(payload.ts), event);
    window.dispatchEvent(new Event("learning-progress-queued"));
  }
  function queueProgressSave(reason){
    saveProgress(reason).catch(() => {});
  }
  function shuffle(a0){ const a=a0.slice(); for(let i=a.length-1;i>0;i--){ const j=(Math.random()*(i+1))|0; [a[i],a[j]]=[a[j],a[i]];} return a; }

  let root, wordBox, progress, answerSlots, lettersPool;
  let builder, builderControls, navRow;
  let btnClear, btnUndo, btnCheck, btnPrev, btnNext;
  let modal, modalClose, line1, line2, line3, btnNextWord, diffToggle;
  let modalContent;
  let modalAudioBtn = null;
  let langButtons;
  let starBtn;
  let lessonLearnedToggle;
  let nextLessonBtn, nextLessonModalBtn;
  let deleteWordBtn, deleteConfirmModal, delWordName, delConfirmBtn, delCancelBtn, delErrorMsg;

  let LESSON=""; let ITEMS=[]; let index=0; let current=null;
  let currentLang="nl";
  let availableLanguages = [
    { code:"nl", name:"Dutch", native:"Dutch" },
    { code:"en", name:"English", native:"English" },
    { code:"ru", name:"Russian", native:"Russian" },
  ];
  let correct="";
  let answer=[]; let pool=[]; let usedFrom=[];
  let fireworksFired = false;

  let _advanceLock = false;
  function advanceToNextOnce(){
    if (_advanceLock) return;
    _advanceLock = true;
    closeModal();
    if (current?.learned === true) {
      ITEMS.splice(index, 1);
      if (!ITEMS.length) {
        wordBox.textContent = tr("learn.all_words_learned");
        setPracticeVisible(false);
        progress.textContent = "0 / 0";
      } else {
        if (index >= ITEMS.length) index = 0;
        renderCurrent();
      }
    } else {
      nextWord();
    }
    setTimeout(()=>{ _advanceLock = false; }, 200);
  }

  function pickAudioSrc(obj, lang){
    if (!obj) return "";
    return obj[`audio_${lang}`] || obj[`${lang}_audio`] || "";
  }
  async function ensureAudioForCurrent(lang, force){
    if (!current || !window.AudioWorker?.ensureForWord) return;
    try{
      const up = await window.AudioWorker.ensureForWord(current, lang, { force: !!force });
      if (up && typeof up==="object"){
        const i = ITEMS.findIndex(x=>x.id===current.id);
        if (i>=0) ITEMS[i]=up;
        current = up;
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
    const activeId = current.id;
    let src = pickAudioSrc(current, lang);
    blip(btn);
    if (!src){
      await ensureAudioForCurrent(lang, true);
      if (!current || String(current.id) !== String(activeId)) return;
      src = pickAudioSrc(current, lang);
    }
    if (src){
      try{
        const audio = new Audio(src);
        audio.addEventListener("error", ()=>{
          ensureAudioForCurrent(lang, true).then(()=>{
            if (!current || String(current.id) !== String(activeId)) return;
            const retrySrc = pickAudioSrc(current, lang);
            if (retrySrc){
              new Audio(retrySrc).play().catch(()=>{});
            }
          }).catch(()=>{});
        }, { once: true });
        audio.play().catch(()=>{});
      }catch(e){ console.warn("play failed", e); }
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

  function languageLabel(lang){
    const meta = availableLanguages.find(x => x.code === lang);
    return (meta && (meta.native || meta.name)) || String(lang || "").toUpperCase();
  }

  function lessonHasCompleteLanguage(items, lang){
    if (!Array.isArray(items) || !items.length) return false;
    return items.every(item => String(
      item?.[`${lang}_word`] || item?.[lang] ||
      (lang === "en" ? item?.word_en : "") ||
      (lang === "ru" ? item?.translation_ru : "") ||
      (lang === "nl" ? item?.translation_nl : "") || ""
    ).trim());
  }

  function renderLanguageButtons(languages, items=ITEMS){
    if (Array.isArray(languages)) {
      availableLanguages = languages.filter(meta => meta?.code && lessonHasCompleteLanguage(items, meta.code));
    }
    const switcher = document.querySelector(".lang-switch");
    if (!switcher) return;
    switcher.innerHTML = [
      `<button data-lang="" class="lang-btn">${tr("common.all")}</button>`,
      ...availableLanguages.map(meta => `<button data-lang="${escapeHtml(meta.code)}" class="lang-btn">${escapeHtml(meta.native || meta.name || meta.code.toUpperCase())}</button>`)
    ].join("");
    langButtons = $$(".lang-switch .lang-btn");
    langButtons.forEach(btn=> btn.addEventListener("click", ()=> setLanguage(btn.dataset.lang||"")));
    if (currentLang !== "all" && !availableLanguages.some(x => x.code === currentLang)) {
      currentLang = availableLanguages[0]?.code || "all";
    }
    setLanguage(currentLang);
  }

  function applyLessonItems(items){
    const available = items.filter(item => item?.learned !== true);
    if (!available.length){ wordBox.textContent=tr("learn.all_words_learned"); return false; }
    ITEMS = available; index=0;
    ITEMS.forEach(x=>{ x._passed = false; });
    fireworksFired = false;
    try{ window.AudioWorker?.warmup?.(); }catch(e){}
    setLanguage(currentLang);
    renderCurrent();
    if (currentLang!=="all") ensureAudioForCurrent(currentLang);
    queueProgressSave("load");
    return true;
  }

  async function loadLesson(){
    if (!LESSON){ wordBox.textContent=tr("learn.lesson_not_selected"); return; }
    try{
      let items = await readLessonWordsFromIdb(LESSON);
      const cachedSig = itemsSig(items);
      if (items && items.length){
        applyLessonItems(items);
      } else {
        wordBox.textContent=tr("learn.loading");
      }
      const js = await apiGet("/api/lesson_words?lesson="+encodeURIComponent(LESSON));
      if (!js || js.ok===false){
        if (!items || !items.length){
          wordBox.textContent=tr("learn.words_load_error");
        }
        return;
      }
      const fresh = Array.isArray(js.items) ? js.items : [];
      renderLanguageButtons(Array.isArray(js.languages) ? js.languages : [], fresh);
      await writeLessonWordsToIdb(LESSON, fresh);
      const cachedEmpty = !Array.isArray(items) || items.length === 0;
      if (cachedEmpty || itemsSig(fresh) !== cachedSig){
        applyLessonItems(fresh);
      }
    }catch(e){
      console.error(e);
      if (!ITEMS || !ITEMS.length) wordBox.textContent=tr("common.no_connection_lessons");
    }
  }

  function pickByLang(item){
    const getWord = (lang) => item[`${lang}_word`] || item[lang] || (lang==="en" ? item.word_en : "") || (lang==="ru" ? item.translation_ru : "") || (lang==="nl" ? item.translation_nl : "") || "";
    const getSent = (lang) => item[`${lang}_sentence`] || item[`sentence_${lang}`] || item[`ex_${lang}`] || "";
    const rowFor = (lang, showWord) => ({
      head: `(${escapeHtml(lang)}) ${showWord ? `<b>${escapeHtml(getWord(lang))}</b>` : ""}`,
      sent: getSent(lang),
      lang
    });
    if (currentLang === "all"){
      return { mode:"all", rows:availableLanguages.map(meta => rowFor(meta.code, true)) };
    }
    const correct = (getWord(currentLang)||"").trim() || availableLanguages.map(meta => getWord(meta.code)).find(Boolean) || "";
    return {
      mode:"one",
      correct,
      rows: availableLanguages
        .filter(meta => meta.code !== currentLang)
        .map(meta => rowFor(meta.code, true))
    };
  }

  function renderCurrent(){ current = ITEMS[index]; renderWordCard(); }

  function renderWordCard(){
    if (!current) return;
    const view = pickByLang(current);
    const editable = !!current.editable;
    const makeRow = (r) => `
      <div class="row" style="align-items:center;gap:8px">
        <div${editable ? ` class="editable-text" data-field="word" data-lang="${r.lang}"` : ''}>${r.head}</div>
        <button type="button" class="audio-btn mini" data-play="${r.lang}" title="▶">▶</button>
      </div>
      <div${editable ? ` class="editable-text" data-field="sentence" data-lang="${r.lang}"` : ''} style="margin-bottom:8px">${renderSentence(r.sent||"")}</div>
    `;
    const sentForLang = (lang) => current[`${lang}_sentence`] || current[`sentence_${lang}`] || current[`ex_${lang}`] || "";
    let sentForModal = currentLang !== "all" ? sentForLang(currentLang) : "";
    if (!sentForModal) sentForModal = availableLanguages.map(meta => sentForLang(meta.code)).find(Boolean) || "";

    if (view.mode === "all"){
      setPracticeVisible(false);
      wordBox.innerHTML = view.rows.map(makeRow).join("");
      progress.textContent = `${index + 1} / ${ITEMS.length}`;
      current._sent_for_modal = sentForModal;
      $$("#word-view .audio-btn").forEach(btn=>{
        btn.addEventListener("click", ()=> playAudio(btn.dataset.play||"nl", btn));
      });
      if (editable) $$("#word-view .editable-text").forEach(el => el.addEventListener("click", () => startInlineEdit(el)));
      if (deleteWordBtn) deleteWordBtn.style.display = editable ? "" : "none";
      return;
    }

    setPracticeVisible(true);
    correct = (view.correct || "—").trim();
    wordBox.innerHTML = view.rows.map(makeRow).join("");
    $$("#word-view .audio-btn").forEach(btn=>{
      btn.addEventListener("click", ()=> playAudio(btn.dataset.play||"nl", btn));
    });
    if (editable) $$("#word-view .editable-text").forEach(el => el.addEventListener("click", () => startInlineEdit(el)));
    pool = shuffle(correct.split(""));
    answer = []; usedFrom = [];
    renderSlots();
    renderPool();
    progress.textContent = `${index + 1} / ${ITEMS.length}`;
    current._sent_for_modal = sentForModal;
    updateDifficultUI();
    if (deleteWordBtn) deleteWordBtn.style.display = editable ? "" : "none";
  }

  function renderSlots(){
    const n = correct.length;
    const filled = answer.join("");
    answerSlots.innerHTML = Array.from({length:n})
      .map((_,i)=>{
        const ch = filled[i] || "";
        const filledCls = ch ? " filled clickable" : "";
        return `<div class="slot${filledCls}" data-pos="${i}" title="${ch ? tr("learn.return_letter") : ''}">${escapeHtml(ch)}</div>`;
      }).join("");
    $$("#answer-slots .slot.filled").forEach(div=>{
      div.addEventListener("click", ()=>{
        const pos = Number(div.dataset.pos||"-1");
        if (pos<0) return;
        returnLetterAt(pos);
      });
    });
  }

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
        usedFrom.push(i);
        pool[i] = null;
        renderSlots();
        renderPool();
      });
    });
  }

  function returnLetterAt(pos){
    const ch = answer[pos];
    if (typeof ch !== "string") return;
    const fromIdx = usedFrom[pos];
    if (typeof fromIdx === "number" && pool[fromIdx] === null){
      pool[fromIdx] = ch;
    } else {
      const hole = pool.findIndex(x=>x===null);
      if (hole>=0) pool[hole]=ch; else pool.push(ch);
    }
    answer.splice(pos,1);
    usedFrom.splice(pos,1);
    renderSlots();
    renderPool();
  }

  // ---------------- ⭐ СЛОЖНОЕ СЛОВО ----------------
  function updateDifficultUI(){
    const isDiff = Number(current?.difficult||0) === 1;
    const wid = String(current?.id||"");
    if (diffToggle){
      diffToggle.checked = isDiff;
      diffToggle.dataset.wordId = wid;
    }
    if (starBtn){
      starBtn.classList.toggle("on", isDiff);
      starBtn.setAttribute("aria-pressed", isDiff ? "true" : "false");
      starBtn.title = isDiff ? tr("learn.remove_difficult") : tr("learn.add_difficult");
      starBtn.dataset.wordId = wid;
    }
  }

  async function setDifficultForCurrent(enabled){
    const widStr = (starBtn?.dataset.wordId) || (diffToggle?.dataset.wordId) || String(current?.id||"");
    const widNum = Number(widStr);
    if (!widNum || isNaN(widNum)) {
      console.warn("[difficult] bad word id:", widStr);
      updateDifficultUI();
      return;
    }
    const prev = Number(current.difficult||0)===1;
    current.difficult = enabled ? 1 : 0;
    updateDifficultUI();
    try{
      const js = await apiPost("/api/difficult/user_set", { word_id: widNum, difficult: enabled ? 1 : 0 });
      if (!js || js.ok!==true) throw new Error("bad response");
    }catch(e){
      console.error("[difficult] save failed:", e);
      current.difficult = prev ? 1 : 0;
      updateDifficultUI();
      alert(tr("learn.difficult_save_failed"));
    }
  }
  // --------------------------------------------------

  function checkAnswer() {
    if (currentLang === "all") return;
    if (current?._answerRecorded) return;
    current._answerRecorded = true;
    const user = answer.join("");
    const ok = (user === correct);

    line1.textContent = ok ? tr("learn.correct") : tr("learn.incorrect");

    const _editable = !!current?.editable;
    line2.innerHTML = `${tr("learn.correct_label")} ${
      _editable
        ? `<b><span class="editable-text" data-field="word" data-lang="${currentLang}">${escapeHtml(correct)}</span></b>`
        : `<b>${escapeHtml(correct)}</b>`
    }`;

    // кнопка ▶ рядом со словом
    modalAudioBtn = document.createElement("button");
    modalAudioBtn.id = "modal-audio-btn";
    modalAudioBtn.type = "button";
    modalAudioBtn.className = "audio-btn icon";
    modalAudioBtn.title = "▶";
    modalAudioBtn.textContent = "▶";
    line2.appendChild(modalAudioBtn);

    const _sentText = current._sent_for_modal || "";
    if (_editable) {
      line3.innerHTML = `<span class="editable-text" data-field="sentence" data-lang="${currentLang}">${renderSentence(_sentText)}</span>`;
    } else {
      line3.innerHTML = renderSentence(_sentText);
    }

    // Инлайн-редактирование прямо из модалки результата
    if (_editable) {
      const _wordSpan = line2.querySelector(".editable-text");
      const _sentSpan = line3.querySelector(".editable-text");
      _wordSpan?.addEventListener("click", e => { e.stopPropagation(); startInlineEdit(_wordSpan); });
      _sentSpan?.addEventListener("click", e => { e.stopPropagation(); startInlineEdit(_sentSpan); });
    }

    // прогрев аудио (не блокирует)
    ensureAudioForCurrent(currentLang).catch(()=>{});

    modal.style.display = "block";
    const isLastWord = (index === ITEMS.length - 1);
    if (ok) {
      line1.style.backgroundColor = "#16a34a";
      line1.style.border = "3px solid #15803d";
      line1.style.color = "#fff";
      current._passed = true;
      current.practice_count = Number(current.practice_count || 0) + 1;
      current.learned = current.practice_count >= 10;
      maybeFireworks();
    } else {
      line1.style.backgroundColor = "#dc2626";
      line1.style.border = "3px solid #b91c1c";
      line1.style.color = "#fff";
    }
    line1.style.padding = "8px 12px";
    line1.style.borderRadius = "8px";
    line1.style.textAlign = "center";
    line1.style.fontWeight = "bold";
    if (nextLessonModalBtn) nextLessonModalBtn.style.display = isLastWord ? "" : "none";
    if (isLastWord && !fireworksFired) {
      fireworksFired = true;
      runFireworks(3000);
    }
    updateDifficultUI();
    queueProgressSave(ok ? "answer_ok" : "answer_fail");
    if (ok) {
      if (typeof window.updateChildGoalOptimistic === "function") {
        window.updateChildGoalOptimistic();
      } else {
        window.dispatchEvent(new Event("child-progress-updated"));
      }
    }

    // обработчик клика по ▶
    if (modalAudioBtn){
      modalAudioBtn.addEventListener("click", (e)=>{
        e.stopPropagation();
        playAudio(currentLang, modalAudioBtn);
      });
    }
  }

  function closeModal(){ modal.style.display="none"; }
  function clearAnswer(){ answer=[]; usedFrom=[]; renderWordCard(); }
  function undo(){
    if (!answer.length) return;
    const ch = answer.pop();
    const fromIdx = usedFrom.pop();
    if (typeof fromIdx === "number" && pool[fromIdx]===null){
      pool[fromIdx] = ch;
    } else {
      const hole = pool.findIndex(x=>x===null);
      if (hole>=0) pool[hole]=ch; else pool.push(ch);
    }
    renderSlots();
    renderPool();
  }
  function prevWord(){
    index = (index - 1 + ITEMS.length) % ITEMS.length;
    ITEMS[index]._answerRecorded = false;
    renderCurrent();
    queueProgressSave("navigate");
  }
  function nextWord(){
    index = (index + 1) % ITEMS.length;
    ITEMS[index]._answerRecorded = false;
    renderCurrent();
    queueProgressSave("navigate");
  }

  function maybeFireworks(){
    if (fireworksFired) return;
    const allPassed = ITEMS.length>0 && ITEMS.every(x=>x._passed === true);
    if (!allPassed) return;
    fireworksFired = true;
    runFireworks(3000);
  }
  function runFireworks(durationMs){
    const canvas = document.createElement('canvas');
    canvas.id = 'fw-canvas';
    document.body.appendChild(canvas);
    const ctx = canvas.getContext('2d');
    let W, H;
    function resize(){ W = canvas.width = innerWidth; H = canvas.height = innerHeight; }
    resize(); addEventListener('resize', resize);
    const particles = [];
    function spawnBurst(x, y){
      const n = 60;
      for (let i=0;i<n;i++){
        const a = Math.random()*Math.PI*2;
        const s = Math.random()*4 + 2;
        particles.push({ x, y, vx: Math.cos(a)*s, vy: Math.sin(a)*s - 2, life: 60 + (Math.random()*30|0), alpha: 1 });
      }
    }
    for (let i=0;i<5;i++){ spawnBurst(Math.random()*W*0.8+W*0.1, Math.random()*H*0.4+H*0.1); }
    let stopAt = performance.now() + durationMs;
    function frame(t){
      ctx.clearRect(0,0,W,H);
      if (Math.random() < 0.06) spawnBurst(Math.random()*W*0.9+W*0.05, Math.random()*H*0.6+H*0.05);
      for (let i=particles.length-1;i>=0;i--){
        const p = particles[i];
        p.vy += 0.03;
        p.x += p.vx;  p.y += p.vy;
        p.life--; p.alpha = Math.max(0, p.life/90);
        ctx.globalAlpha = p.alpha;
        ctx.beginPath(); ctx.arc(p.x, p.y, 2.2, 0, Math.PI*2); ctx.fill();
        if (p.life<=0 || p.alpha<=0) particles.splice(i,1);
      }
      ctx.globalAlpha = 1;
      if (t < stopAt) requestAnimationFrame(frame);
      else { removeEventListener('resize', resize); canvas.remove(); }
    }
    requestAnimationFrame(frame);
  }

  // ---- Инлайн-редактирование конкретного поля слова ----
  function getFieldValue(item, lang, field) {
    if (field === "word") {
      return item[`${lang}_word`] || item[lang] || (lang === "nl" ? item.translation_nl : "") || (lang === "en" ? item.word_en : "") || (lang === "ru" ? item.translation_ru : "") || "";
    }
    return item[`${lang}_sentence`] || item[`sentence_${lang}`] || item[`ex_${lang}`] || "";
  }

  function applyWordUpdate(item, w) {
    availableLanguages.forEach(meta => {
      const lang = meta.code;
      const word = w[`${lang}_word`] ?? w[lang];
      if (word !== undefined) {
        item[`${lang}_word`] = word;
        item[lang] = word;
        if (lang === "nl") item.translation_nl = word;
        if (lang === "en") item.word_en = word;
        if (lang === "ru") item.translation_ru = word;
      }
      const sentence = w[`${lang}_sentence`] ?? w[`sentence_${lang}`] ?? w[`ex_${lang}`];
      if (sentence !== undefined) {
        item[`${lang}_sentence`] = sentence;
        item[`sentence_${lang}`] = sentence;
        item[`ex_${lang}`] = sentence;
      }
      const audio = w[`${lang}_audio`] ?? w[`audio_${lang}`];
      if (audio !== undefined) {
        item[`${lang}_audio`] = audio;
        item[`audio_${lang}`] = audio;
      }
    });
  }

  function startInlineEdit(el) {
    if (!current || !current.id) return;
    if (el.isContentEditable) return; // уже редактируется

    const field   = el.dataset.field; // "word" | "sentence"
    const lang    = el.dataset.lang;  // "nl" | "en" | "ru"
    const dbField = field === "word" ? lang : `ex_${lang}`;
    const origValue = getFieldValue(current, lang, field);
    const origHTML  = el.innerHTML;

    // contenteditable надёжно вызывает клавиатуру на мобильных
    el.contentEditable = "true";
    el.setAttribute("spellcheck", "false");
    el.setAttribute("autocorrect", "off");
    el.setAttribute("autocapitalize", "none");
    el.setAttribute("autocomplete", "off");
    el.textContent = origValue;
    el.classList.add("inline-editing");
    el.focus();

    // Выделить весь текст
    try {
      const range = document.createRange();
      range.selectNodeContents(el);
      const sel = window.getSelection();
      if (sel) { sel.removeAllRanges(); sel.addRange(range); }
    } catch(_) {}

    let done = false;

    function stopEdit() {
      el.contentEditable = "false";
      el.classList.remove("inline-editing");
      el.removeAttribute("spellcheck");
      el.removeAttribute("autocorrect");
      el.removeAttribute("autocapitalize");
      el.removeAttribute("autocomplete");
    }

    async function commit() {
      if (done) return;
      done = true;
      stopEdit();
      const newVal = (el.textContent || "").trim();
      if (newVal === origValue.trim()) { renderCurrent(); return; }
      el.textContent = newVal; // оптимистичный показ
      try {
        const r = await window.apiFetch(`/api/words/${current.id}`, {
          method: "PUT",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({ [dbField]: newVal })
        });
        const js = await r.json();
        if (!js || js.ok !== true) throw new Error(js?.error || tr("common.error"));
        applyWordUpdate(current, js.word || {});
        const i = ITEMS.findIndex(x => x.id === current.id);
        if (i >= 0) ITEMS[i] = current;
        writeLessonWordsToIdb(LESSON, ITEMS).catch(() => {});
        renderCurrent();
      } catch(e) {
        console.error("[inline-edit]", e);
        el.innerHTML = origHTML; // откат при ошибке
      }
    }

    function cancel() {
      if (done) return;
      done = true;
      stopEdit();
      renderCurrent();
    }

    function onKeydown(e) {
      if (e.key === "Enter")  { e.preventDefault(); el.removeEventListener("keydown", onKeydown); commit(); }
      if (e.key === "Escape") { e.preventDefault(); el.removeEventListener("keydown", onKeydown); cancel(); }
      e.stopPropagation();
    }

    el.addEventListener("keydown", onKeydown);
    el.addEventListener("blur", () => {
      el.removeEventListener("keydown", onKeydown);
      commit();
    }, { once: true });
  }
  // ----------------------------------

  async function goToNextLesson(){
    try{
      const js = await apiGet("/api/next_lesson?current=" + encodeURIComponent(LESSON));
      if (js && js.ok && js.next){ location.href = "/learn?lesson=" + encodeURIComponent(js.next); }
      else { location.href = "/lessons"; }
    }catch(_){ location.href = "/lessons"; }
  }

  async function syncLessonLearnedToggle(){
    if (!lessonLearnedToggle || !LESSON) return;
    try{
      let lessons = await readLessonsFromIdb();
      if (!lessons) {
        lessons = await apiGet("/api/lessons");
        if (Array.isArray(lessons)) await writeLessonsToIdb(lessons);
      }
      if (!Array.isArray(lessons)) return;
      const found = lessons.find((x)=> (x.lesson || x.lesson_title || "") === LESSON);
      if (!found) return;
      lessonLearnedToggle.checked = Number(found.hidden || 0) === 1;
    }catch(e){
      console.warn("[lesson] failed to load lesson status", e);
    }
  }

  async function saveLessonLearnedToggle(checked){
    if (!lessonLearnedToggle) return;
    const lesson = lessonLearnedToggle.dataset.lesson || LESSON;
    if (!lesson) return;
    const hidden = checked ? 1 : 0;
    try{
      const resp = await window.apiFetch("/api/lessons/set_hidden", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ lesson, hidden })
      });
      if (!resp.ok) throw new Error("server error");
      await updateLessonHiddenCache(lesson, hidden);
    }catch(e){
      lessonLearnedToggle.checked = !checked;
    }
  }

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
    modalContent = $("#modal-content");
    diffToggle = $("#difficultToggle");
    starBtn    = $("#difficultStar");
    lessonLearnedToggle = $("#lesson-learned-toggle");

    langButtons = $$(".lang-switch .lang-btn");
    nextLessonBtn = $("#next-lesson-btn");
    nextLessonModalBtn = $("#next-lesson-modal-btn");

    deleteWordBtn      = $("#delete-word-btn");
    deleteConfirmModal = $("#delete-confirm-modal");
    delWordName        = $("#del-word-name");
    delConfirmBtn      = $("#del-confirm-btn");
    delCancelBtn       = $("#del-cancel-btn");
    delErrorMsg        = $("#del-error-msg");

    LESSON = (root && root.dataset.lesson) || window.LESSON_TITLE || "";

    if (lessonLearnedToggle){
      if (LESSON){
        if (!lessonLearnedToggle.dataset.lesson) lessonLearnedToggle.dataset.lesson = LESSON;
        lessonLearnedToggle.addEventListener("change", (e)=> saveLessonLearnedToggle(!!e.target.checked));
        syncLessonLearnedToggle();
      } else {
        lessonLearnedToggle.disabled = true;
      }
    }

    btnClear?.addEventListener("click", clearAnswer);
    btnUndo?.addEventListener("click", undo);
    btnPrev?.addEventListener("click", prevWord);
    btnNext?.addEventListener("click", nextWord);
    btnCheck?.addEventListener("click", checkAnswer);
    modalClose?.addEventListener("click", closeModal);

    btnNextWord?.addEventListener("click", (e)=>{
      e.stopPropagation();
      advanceToNextOnce();
    });

    if (modalContent){
      modalContent.addEventListener("click", (e)=>{
        const t = e.target;
        if (
          t.id === "modal-close" ||
          t.id === "next-lesson-modal-btn" ||
          t.id === "next-word-btn" ||
          t.closest?.("#modal-close") ||
          t.closest?.("#next-lesson-modal-btn") ||
          t.closest?.("#next-word-btn") ||
          t.closest?.(".flag-toggle") ||
          t.closest?.(".editable-text") ||
          t.closest?.("button")
        ){ return; }
        advanceToNextOnce();
      });
    }
    line1?.addEventListener("click", ()=> advanceToNextOnce());
    line2?.addEventListener("click", (e)=> { if (!e.target.closest?.(".editable-text")) advanceToNextOnce(); });
    line3?.addEventListener("click", (e)=> { if (!e.target.closest?.(".editable-text")) advanceToNextOnce(); });

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

    if (nextLessonBtn){ nextLessonBtn.addEventListener("click", (e)=>{ e.preventDefault(); goToNextLesson(); }); }
    if (nextLessonModalBtn){ nextLessonModalBtn.addEventListener("click", (e)=>{ e.stopPropagation(); goToNextLesson(); }); }

    // ── Удаление слова ──────────────────────────────────────────
    deleteWordBtn?.addEventListener("click", ()=>{
      if (!current || !current.editable) return;
      const label = current.translation_nl || current.nl_word || current.word_en || current.en_word || tr("learn.delete_word");
      if (delWordName) delWordName.textContent = `«${label}»`;
      if (delErrorMsg) delErrorMsg.textContent = "";
      if (deleteConfirmModal) deleteConfirmModal.style.display = "";
    });

    delCancelBtn?.addEventListener("click", ()=>{
      if (deleteConfirmModal) deleteConfirmModal.style.display = "none";
    });

    deleteConfirmModal?.addEventListener("click", (e)=>{
      if (e.target === deleteConfirmModal) deleteConfirmModal.style.display = "none";
    });

    delConfirmBtn?.addEventListener("click", async ()=>{
      if (!current || !current.id) { if (deleteConfirmModal) deleteConfirmModal.style.display = "none"; return; }
      delConfirmBtn.disabled = true;
      if (delErrorMsg) delErrorMsg.textContent = "";
      try {
        const r = await window.apiFetch(`/api/words/${current.id}`, { method: "DELETE" });
        const js = await r.json();
        if (!js || !js.ok) throw new Error(js?.error || tr("learn.delete_error"));

        ITEMS.splice(index, 1);
        writeLessonWordsToIdb(LESSON, ITEMS).catch(()=>{});
        if (deleteConfirmModal) deleteConfirmModal.style.display = "none";

        if (!ITEMS.length) {
          wordBox.textContent = tr("learn.no_words_in_lesson");
          setPracticeVisible(false);
          if (progress) progress.textContent = "0 / 0";
          if (deleteWordBtn) deleteWordBtn.style.display = "none";
          return;
        }
        if (index >= ITEMS.length) index = ITEMS.length - 1;
        renderCurrent();
      } catch(e) {
        if (delErrorMsg) delErrorMsg.textContent = tr("common.error") + ": " + (e.message || tr("learn.delete_failed"));
      } finally {
        delConfirmBtn.disabled = false;
      }
    });

    loadLesson();
  });
})();
