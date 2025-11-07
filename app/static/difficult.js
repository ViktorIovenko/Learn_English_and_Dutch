/* app/static/difficult.js
 * [v8.22] Аудио в модалке результата: кнопка ▶ воспроизводит правильное слово на текущем языке (как в learn.js v8.24).
 * [v8.21] Полный паритет с learn.js:
 *  - анти-дубль перехода advanceToNextOnce() (не перескакивает через слово)
 *  - клик по заполненному слоту возвращает букву (usedFrom[] для точного возврата)
 *  - клик по области модалки = следующее слово (кнопки/иконки игнорируются)
 *  - фейерверк на последнем слове списка
 * [FIX] Исправлены кавычки в line1.style.border (ошибка парсинга ломала весь скрипт)
 */
(function () {
  const $  = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));
  function escapeHtml(s){ return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
  async function apiGet(url){ const r = await (window.apiFetch?window.apiFetch(url):fetch(url)); return r.json(); }
  async function apiPost(url, body){
    const r = await (window.apiFetch?window.apiFetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body||{})})
                                 :fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body||{})}));
    return r.json();
  }
  function shuffle(a0){ const a=a0.slice(); for(let i=a.length-1;i>0;i--){ const j=(Math.random()*(i+1))|0; [a[i],a[j]]=[a[j],a[i]];} return a; }

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
  const modalContent = $("#modal-content");
  const line1        = $("#modal-line1");
  const line2        = $("#modal-line2");
  const line3        = $("#modal-line3");
  const btnNextWord  = $("#next-word-btn");
  const diffToggle   = $("#difficultToggle");
  const langButtons  = $$(".lang-switch .lang-btn");

  // [ДОБАВЛЕНО v8.22] Кнопка аудио в модалке
  let modalAudioBtn = null;

  let ITEMS=[], index=0, current=null;
  let currentLang="nl";
  let correct=""; let answer=[]; let pool=[]; let usedFrom=[];
  let fireworksFired=false;

  // анти-дубль
  let _advanceLock=false;
  function advanceToNextOnce(){
    if (_advanceLock) return;
    _advanceLock=true;
    closeModal();
    nextWord();
    setTimeout(()=>{ _advanceLock=false; },200);
  }

  function pickAudioSrc(obj,lang){
    if (!obj) return "";
    if (lang==="nl") return obj.audio_nl || obj.nl_audio || "";
    if (lang==="en") return obj.audio_en || obj.en_audio || "";
    if (lang==="ru") return obj.audio_ru || obj.ru_audio || "";
    return "";
  }
  function blip(btn){
    if(!btn) return;
    btn.classList.remove("playing"); void btn.offsetWidth;
    btn.classList.add("playing"); setTimeout(()=>btn.classList.remove("playing"),650);
  }
  async function ensureAudioForCurrent(lang){
    if (!current || !window.AudioWorker?.ensureForWord) return;
    try{
      const up = await window.AudioWorker.ensureForWord(current, lang);
      if (up && typeof up==="object"){
        const i = ITEMS.findIndex(x=>String(x.id)===String(current.id));
        if (i>=0) ITEMS[i]=up;
        current = up;
      }
    }catch(e){ console.warn("[Audio] ensureForWord failed", e); }
  }
  async function playAudio(lang, btn){
    if (!current) return;
    let src = pickAudioSrc(current, lang);
    blip(btn);
    if (!src){ await ensureAudioForCurrent(lang); src = pickAudioSrc(current, lang); }
    if (src){ try{ new Audio(src).play().catch(()=>{}); }catch(e){ console.warn("play failed", e); } }
  }

  function setPracticeVisible(show){
    if (answerSlots)     answerSlots.style.display     = show ? "" : "none";
    if (lettersPool)     lettersPool.style.display     = show ? "" : "none";
    if (builderControls) builderControls.style.display = show ? "" : "none";
    if (navRow)          navRow.style.display          = "";
  }

  async function loadDifficult(){
    wordBox.textContent="Загрузка...";
    try{
      const js = await apiGet("/api/difficult_words_user");
      const items = (js && js.items) ? js.items : [];
      if (!items.length){
        wordBox.textContent="У вас пока нет отмеченных сложных слов.";
        progress.textContent="0 / 0";
        setPracticeVisible(false);
        return;
      }
      ITEMS = items; index=0; fireworksFired=false;
      try{ window.AudioWorker?.warmup?.(); }catch(e){}
      setLanguage(currentLang);
      renderCurrent();
      if (currentLang!=="all") ensureAudioForCurrent(currentLang);
    }catch(e){
      console.error(e);
      wordBox.textContent="Не удалось загрузить список. Проверьте сеть.";
      setPracticeVisible(false);
    }
  }

  function setLanguage(langRaw){
    const norm = (langRaw==="" || langRaw==null) ? "all" : (langRaw || "nl");
    currentLang = norm;
    langButtons.forEach(b=>{
      const dl = b.dataset.lang || "";
      const btnNorm = (dl==="" ? "all" : dl);
      b.classList.toggle("active", btnNorm===currentLang);
    });
    if (ITEMS.length){
      renderCurrent();
      if (currentLang!=="all") ensureAudioForCurrent(currentLang);
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
      $$("#word-view .audio-btn").forEach(btn=> btn.addEventListener("click", ()=> playAudio(btn.dataset.play||"nl", btn)));
      return;
    }

    setPracticeVisible(true);
    correct = (view.correct || "—").trim();
    wordBox.innerHTML = view.rows.map(makeRow).join("");
    $$("#word-view .audio-btn").forEach(btn=> btn.addEventListener("click", ()=> playAudio(btn.dataset.play||"nl", btn)));

    pool = shuffle(correct.split(""));
    answer = []; usedFrom = [];
    renderSlots();
    renderPool();
    progress.textContent = `${index + 1} / ${ITEMS.length}`;
    current._sent_for_modal = sentForModal;
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

  async function setPersonalDifficult(enabled){
    const id = diffToggle.dataset.id || "";
    try{
      const wid = Number(id);
      if (!wid || isNaN(wid)) throw new Error("bad id");
      const js = await apiPost("/api/difficult/user_set",{ word_id: wid, difficult: enabled ? 1 : 0 });
      if (!js || js.ok !== true) throw new Error("bad response");
      current.difficult = enabled ? 1 : 0;
      if (!enabled){
        // убрать слово из списка (оно перестало быть сложным)
        ITEMS = ITEMS.filter(x => String(x.id) !== String(id));
        if (!ITEMS.length){
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
    }catch(e){
      console.error(e);
      diffToggle.checked = !enabled;
      alert("Не удалось сохранить статус «сложное слово». Повторите позже.");
    }
  }

  function updateDiffToggleUI(){
    diffToggle.checked = Number(current?.difficult || 1) === 1;
    diffToggle.dataset.id = String(current?.id || "");
  }

  function checkAnswer(){
    if (currentLang === "all") return;
    const user = answer.join("");
    const ok = (user === correct);

    line1.textContent = ok ? "Правильно!" : "Неправильно!";
    line2.innerHTML = `Правильно: <b>${escapeHtml(correct)}</b>`;

    // [ДОБАВЛЕНО v8.22] — вставляем кнопку ▶ прямо в строку рядом со словом
    modalAudioBtn = document.createElement("button");
    modalAudioBtn.id = "modal-audio-btn";
    modalAudioBtn.type = "button";
    modalAudioBtn.className = "audio-btn icon";
    modalAudioBtn.title = "▶";
    modalAudioBtn.textContent = "▶";
    line2.appendChild(modalAudioBtn);

    line3.textContent = current._sent_for_modal || "";

    // [ДОБАВЛЕНО] прогрев аудио (не блокирует)
    ensureAudioForCurrent(currentLang).catch(()=>{});

    updateDiffToggleUI();
    modal.style.display = "block";

    const isLastWord = (index === ITEMS.length - 1);
    if (ok){
      line1.style.backgroundColor = "#16a34a";
      line1.style.border = "3px solid #15803d";   // ✔ исправлено ранее
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

    if (isLastWord && !fireworksFired){
      fireworksFired = true;
      runFireworks(3000);
    }

    // [ДОБАВЛЕНО v8.22] обработчик клика по ▶ (не закрывать модалку)
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

  function runFireworks(durationMs){
    const canvas = document.createElement('canvas');
    canvas.id = 'fw-canvas';
    document.body.appendChild(canvas);
    const ctx = canvas.getContext('2d');
    let W,H; function resize(){ W=canvas.width=innerWidth; H=canvas.height=innerHeight; }
    resize(); addEventListener('resize', resize);
    const particles=[];
    function spawnBurst(x,y){
      const n=60;
      for(let i=0;i<n;i++){
        const a=Math.random()*Math.PI*2, s=Math.random()*4+2;
        particles.push({x,y,vx:Math.cos(a)*s,vy:Math.sin(a)*s-2,life:60+(Math.random()*30|0),alpha:1});
      }
    }
    for(let i=0;i<5;i++){ spawnBurst(Math.random()*W*0.8+W*0.1, Math.random()*H*0.4+H*0.1); }
    const stopAt=performance.now()+durationMs;
    function frame(t){
      ctx.clearRect(0,0,W,H);
      if (Math.random()<0.06) spawnBurst(Math.random()*W*0.9+W*0.05, Math.random()*H*0.6+H*0.05);
      for (let i=particles.length-1;i>=0;i--){
        const p=particles[i]; p.vy+=0.03; p.x+=p.vx; p.y+=p.vy; p.life--; p.alpha=Math.max(0,p.life/90);
        ctx.globalAlpha=p.alpha; ctx.beginPath(); ctx.arc(p.x,p.y,2.2,0,Math.PI*2); ctx.fill();
        if (p.life<=0 || p.alpha<=0) particles.splice(i,1);
      }
      ctx.globalAlpha=1;
      if (t<stopAt) requestAnimationFrame(frame);
      else { removeEventListener('resize', resize); canvas.remove(); }
    }
    requestAnimationFrame(frame);
  }

  // слушатели
  btnClear.addEventListener("click", clearAnswer);
  btnUndo.addEventListener("click", undo);
  btnPrev.addEventListener("click", prevWord);
  btnNext.addEventListener("click", nextWord);
  btnCheck.addEventListener("click", checkAnswer);
  modalClose.addEventListener("click", closeModal);
  btnNextWord.addEventListener("click", (e)=>{ e.stopPropagation(); advanceToNextOnce(); });

  if (modalContent){
    modalContent.addEventListener("click", (e)=>{
      const t=e.target;
      if (t.id==="modal-close" || t.id==="next-word-btn" ||
          t.closest?.("#modal-close") || t.closest?.("#next-word-btn") ||
          t.closest?.(".flag-toggle") || t.closest?.("button")) return;
      advanceToNextOnce();
    });
  }
  line1.addEventListener("click", ()=>advanceToNextOnce());
  line2.addEventListener("click", ()=>advanceToNextOnce());
  line3.addEventListener("click", ()=>advanceToNextOnce());

  diffToggle.addEventListener("change", (e)=> setPersonalDifficult(!!e.target.checked));
  langButtons.forEach(btn=> btn.addEventListener("click", ()=> setLanguage(btn.dataset.lang||"")));

  const btnNl = document.querySelector('.lang-switch .lang-btn[data-lang="nl"]');
  if (btnNl) btnNl.classList.add("active");
  currentLang="nl";

  loadDifficult();
})();
