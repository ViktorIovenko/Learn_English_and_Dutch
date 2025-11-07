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
  let modalContent;
  let modalAudioBtn = null;        // [ОБНОВЛЕНО v8.24]
  let langButtons;
  let starBtn;
  let nextLessonBtn, nextLessonModalBtn;

  let LESSON=""; let ITEMS=[]; let index=0; let current=null;
  let currentLang="nl";
  let correct="";
  let answer=[]; let pool=[]; let usedFrom=[];
  let fireworksFired = false;

  let _advanceLock = false;
  function advanceToNextOnce(){
    if (_advanceLock) return;
    _advanceLock = true;
    closeModal();
    nextWord();
    setTimeout(()=>{ _advanceLock = false; }, 200);
  }

  function pickAudioSrc(obj, lang){
    if (!obj) return "";
    if (lang==="nl") return obj.audio_nl||"";
    if (lang==="en") return obj.audio_en||"";
    if (lang==="ru") return obj.audio_ru||"";
    return "";
  }
  async function ensureAudioForCurrent(lang){
    if (!current || !window.AudioWorker?.ensureForWord) return;
    try{
      const up = await window.AudioWorker.ensureForWord(current, lang);
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
      ITEMS.forEach(x=>{ x._passed = false; });
      fireworksFired = false;
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
    const nlS = current.sentence_nl || "";
    const enS = current.sentence_en || "";
    const ruS = current.sentence_ru || "";
    let sentForModal = "";
    if (currentLang === "nl") sentForModal = nlS;
    else if (currentLang === "en") sentForModal = enS;
    else if (currentLang === "ru") sentForModal = ruS;
    if (!sentForModal) sentForModal = nlS || enS || ruS || "";

    if (view.mode === "all"){
      setPracticeVisible(false);
      wordBox.innerHTML = view.rows.map(makeRow).join("");
      progress.textContent = `${index + 1} / ${ITEMS.length}`;
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
    answer = []; usedFrom = [];
    renderSlots();
    renderPool();
    progress.textContent = `${index + 1} / ${ITEMS.length}`;
    current._sent_for_modal = sentForModal;
    updateDifficultUI();
  }

  function renderSlots(){
    const n = correct.length;
    const filled = answer.join("");
    answerSlots.innerHTML = Array.from({length:n})
      .map((_,i)=>{
        const ch = filled[i] || "";
        const filledCls = ch ? " filled clickable" : "";
        return `<div class="slot${filledCls}" data-pos="${i}" title="${ch ? 'Нажмите, чтобы вернуть букву' : ''}">${escapeHtml(ch)}</div>`;
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
      starBtn.title = isDiff ? "Убрать из сложных" : "Добавить в сложные";
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
      alert("Не удалось сохранить статус «сложное слово». Проверьте соединение и попробуйте ещё раз.");
    }
  }
  // --------------------------------------------------

  function checkAnswer() {
    if (currentLang === "all") return;
    const user = answer.join("");
    const ok = (user === correct);

    line1.textContent = ok ? "Правильно!" : "Неправильно!";
    line2.innerHTML = `Правильно: <b>${escapeHtml(correct)}</b>`;

    // [ДОБАВЛЕНО v8.24] — вставляем кнопку ▶ прямо в строку рядом со словом
    modalAudioBtn = document.createElement("button");
    modalAudioBtn.id = "modal-audio-btn";
    modalAudioBtn.type = "button";
    modalAudioBtn.className = "audio-btn icon";
    modalAudioBtn.title = "▶";
    modalAudioBtn.textContent = "▶";
    line2.appendChild(modalAudioBtn);

    line3.textContent = current._sent_for_modal || "";

    // прогрев аудио (не блокирует)
    ensureAudioForCurrent(currentLang).catch(()=>{});

    modal.style.display = "block";
    const isLastWord = (index === ITEMS.length - 1);
    if (ok) {
      line1.style.backgroundColor = "#16a34a";
      line1.style.border = "3px solid #15803d";
      line1.style.color = "#fff";
      current._passed = true;
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
  function prevWord(){ index = (index - 1 + ITEMS.length) % ITEMS.length; renderCurrent(); }
  function nextWord(){ index = (index + 1) % ITEMS.length; renderCurrent(); }

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

  async function goToNextLesson(){
    try{
      const js = await apiGet("/api/next_lesson?current=" + encodeURIComponent(LESSON));
      if (js && js.ok && js.next){ location.href = "/learn?lesson=" + encodeURIComponent(js.next); }
      else { location.href = "/lessons"; }
    }catch(_){ location.href = "/lessons"; }
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

    langButtons = $$(".lang-switch .lang-btn");
    nextLessonBtn = $("#next-lesson-btn");
    nextLessonModalBtn = $("#next-lesson-modal-btn");

    LESSON = (root && root.dataset.lesson) || window.LESSON_TITLE || "";

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
          t.closest?.("button")
        ){ return; }
        advanceToNextOnce();
      });
    }
    line1?.addEventListener("click", ()=> advanceToNextOnce());
    line2?.addEventListener("click", ()=> advanceToNextOnce());
    line3?.addEventListener("click", ()=> advanceToNextOnce());

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

    loadLesson();
  });
})();
