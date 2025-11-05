(function () {
  window.__LEARN_BOOTED__ = true;
  // ---------- helpers ----------
  function $(sel, root = document) { return root.querySelector(sel); }
  function $all(sel, root = document) { return Array.from(root.querySelectorAll(sel)); }
  function audioPlay(src) { if (!src) return; new Audio(src).play().catch(()=>{}); }
  function escapeHtml(s){ return (s||'').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])); }
  function shuffle(a){ for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];} }
  function api(url, opts){ return (window.apiFetch ? window.apiFetch(url, opts) : fetch(url, opts)); }

  // [ИЗМЕНЕНО v7.1] генерация «шума» с учётом языка слова
  function randNoises(n, target){
    const hasCyrillic = /[А-Яа-яЁё]/.test(target || '');
    const pool = hasCyrillic
      ? 'аеиорнстлумкдпбвгязйчшхцфжыё'
      : 'aeiourtnslmdpbgch';
    const out = [];
    while(out.length < n){ out.push(pool[Math.floor(Math.random() * pool.length)]); }
    return out;
  }

  // ---------- root ----------
  const root = document.getElementById('learn-root');
  if (!root) { console.error('[learn] #learn-root не найден'); return; }
  function fromQuery() { try { return new URLSearchParams(location.search).get('lesson') || ''; } catch(e){ return ''; } }
  const lessonTitle =
    (root.dataset && root.dataset.lesson ? root.dataset.lesson : '') ||
    (typeof window.LESSON_TITLE !== 'undefined' ? window.LESSON_TITLE : '') ||
    fromQuery();
  if (!lessonTitle) { console.error('[learn] lessonTitle пуст'); return; }

  // ui
  const wordView    = $('#word-view');
  const lettersPool = $('#letters-pool');
  const answerSlots = $('#answer-slots');
  const progressEl  = $('#progress');
  const undoBtn     = $('#undo-btn');
  const clearBtn    = $('#clear-btn');
  const checkBtn    = $('#check-btn');
  const prevBtn     = $('#prev-btn');
  const nextBtn     = $('#next-btn');
  const builderCtrls= $('.builder-controls');

  // [ДОБАВЛЕНО v7.2] элементы модалки
  const resultModal = $('#result-modal');
  const modalClose  = $('#modal-close');
  const nextWordBtn = $('#next-word-btn');
  // [ДОБАВЛЕНО v7.5] чекбокс «сложное»
  const diffToggle  = $('#difficultToggle');

  // state
  let learningLanguage = 'nl';   // '': все | 'nl' | 'en' | 'ru'
  let words = [];
  let idx = 0;
  let picked = [];

  // ---------- api ----------
  api(`/api/lesson_words?lesson=${encodeURIComponent(lessonTitle)}`)
    .then(r => r.json())
    .then(data => {
      if (!data || data.ok === false) { if (wordView) wordView.textContent='Ошибка загрузки слов.'; return; }
      words = data.items || [];
      if (!words.length){ if (wordView) wordView.textContent='В этом уроке пока нет слов.'; return; }
      render();
      updateLangButtons();
    })
    .catch(()=>{ if(wordView) wordView.textContent='Ошибка сети при загрузке слов.'; });

  // ---------- rendering ----------
  function render() {
    const w = words[idx];
    if (progressEl) progressEl.textContent = `${idx + 1} / ${words.length}`;

    // карточка: скрываем выбранный язык
    const lines = [];
    const items = [
      { lang:'nl', word:w.translation_nl, sent:w.sentence_nl, audio:w.audio_nl },
      { lang:'en', word:w.word_en,        sent:w.sentence_en, audio:w.audio_en },
      { lang:'ru', word:w.translation_ru, sent:w.sentence_ru, audio:w.audio_ru },
    ];
    items.forEach(it=>{
      const label = ({en:'(en)', ru:'(ru)', nl:'(nl)'}[it.lang]) || '';
      const play  = it.audio ? `<button class="ctrl-btn" onclick="(${audioPlay.toString()})('${it.audio}')">▶</button>` : '';
      if (learningLanguage && it.lang === learningLanguage) return;
      lines.push(`
        <div class="word-block">
          <div class="word-title"><span class="badge">${label}</span> <strong>${escapeHtml(it.word||'')}</strong> ${play}</div>
          <div class="word-sentence">${escapeHtml(it.sent||'')}</div>
        </div>
      `);
    });
    if (wordView) wordView.innerHTML = lines.join('');

    // билдер
    if (!learningLanguage) {
      toggleBuilder(false);
    } else {
      toggleBuilder(true);
      const target = pickTargetWord(w);
      buildLetters(target);
      buildSlots(Array.from(target||'').length);
    }
    if (prevBtn) prevBtn.disabled = (idx === 0);
    if (nextBtn) nextBtn.disabled = (idx === words.length - 1);
  }

  function toggleBuilder(show){
    const dsp = show ? '' : 'none';
    if (answerSlots)  answerSlots.style.display = dsp;
    if (lettersPool)  lettersPool.style.display = dsp;
    if (builderCtrls) builderCtrls.style.display = dsp;
  }
  function pickTargetWord(w) {
    if (learningLanguage === 'en') return w.word_en || '';
    if (learningLanguage === 'ru') return w.translation_ru || '';
    if (learningLanguage === 'nl') return w.translation_nl || '';
    return '';
  }

  // [ИЗМЕНЕНО v7.1] корректное разбиение и «шум»
  function buildLetters(target) {
    picked = [];
    if (lettersPool) lettersPool.innerHTML = '';
    const chars = Array.from(target || '');
    if (chars.length < 6) chars.push(...randNoises(6 - chars.length, target));
    shuffle(chars);
    chars.forEach((ch, i) => {
      const el = document.createElement('div');
      el.className = 'letter clickable';
      el.textContent = ch;
      el.dataset.i = String(i);
      el.addEventListener('click', () => pickLetter(i, ch, el));
      lettersPool && lettersPool.appendChild(el);
    });
  }
  function buildSlots(n) {
    if (answerSlots) answerSlots.innerHTML = '';
    for (let i = 0; i < n; i++) {
      const s = document.createElement('div');
      s.className = 'slot';
      s.dataset.i = String(i);
      answerSlots && answerSlots.appendChild(s);
    }
    if (answerSlots) answerSlots.scrollLeft = 0;
  }
  function pickLetter(fromIndex, ch, el) {
    const slot = answerSlots && answerSlots.querySelector('.slot:not([data-filled="1"])');
    if (!slot) return;
    slot.textContent = ch;
    slot.dataset.filled = '1';
    picked.push({ ch, fromIndex, el });
    el.classList.remove('clickable');
    el.style.opacity = '0.45';
    el.style.pointerEvents = 'none';
  }
  function undo() {
    const last = picked.pop();
    if (!last) return;
    const filled = answerSlots ? Array.from(answerSlots.querySelectorAll('.slot[data-filled="1"]')) : [];
    const s = filled[filled.length - 1];
    if (s) { s.textContent = ''; s.removeAttribute('data-filled'); }
    last.el.style.opacity = '';
    last.el.style.pointerEvents = '';
    last.el.classList.add('clickable');
  }
  function clearAll() {
    picked = [];
    (answerSlots ? Array.from(answerSlots.querySelectorAll('.slot')) : []).forEach(s => {
      s.textContent = '';
      s.removeAttribute('data-filled');
    });
    (lettersPool ? Array.from(lettersPool.querySelectorAll('.letter')) : []).forEach(el => {
      el.style.opacity = '';
      el.style.pointerEvents = '';
      el.classList.add('clickable');
    });
  }

  // ------ Проверка + модалка ------
  function check() {
    const w = words[idx];
    const target = pickTargetWord(w);
    const user = (answerSlots ? Array.from(answerSlots.querySelectorAll('.slot')) : [])
                   .map(s=>s.textContent||'').join('');
    const ok = (user.toLocaleLowerCase('ru') === (target||'').toLocaleLowerCase('ru'));
    const sentence = pickSentence(w);
    const head = ok ? '<strong>Правильно!</strong>' : '<strong>Неправильно!</strong>';
    showModal(head, `Правильно: <strong>${escapeHtml(target)}</strong>`, escapeHtml(sentence), wAudio(w));
    // [ДОБАВЛЕНО v7.5] проставляем чекбокс для текущего слова
    if (diffToggle && typeof w.difficult !== 'undefined') {
      diffToggle.checked = !!w.difficult;
    }
  }
  function wAudio(w) {
    if (learningLanguage === 'en') return w.audio_en || '';
    if (learningLanguage === 'ru') return w.audio_ru || '';
    return w.audio_nl || '';
  }
  function pickSentence(w) {
    if (learningLanguage === 'en') return w.sentence_en || '';
    if (learningLanguage === 'ru') return w.sentence_ru || '';
    return w.sentence_nl || '';
  }
  function showModal(line1, line2, line3, audioSrc) {
    if (!resultModal) return;
    const l1 = $('#modal-line1'), l2 = $('#modal-line2'), l3 = $('#modal-line3');
    if (l1) l1.innerHTML = line1;
    if (l2) l2.innerHTML = `${line2} ${audioSrc ? `<button class="ctrl-btn" onclick="(${audioPlay.toString()})('${audioSrc}')">▶</button>` : ''}`;
    if (l3) l3.textContent = line3;
    resultModal.style.display = 'flex';
    resultModal.classList.add('show');
    document.documentElement.style.overflow = 'hidden';
    document.body.style.overflow = 'hidden';
    if (nextWordBtn) nextWordBtn.focus();
  }
  function hideModal() {
    if (!resultModal) return;
    resultModal.classList.remove('show');
    resultModal.style.display = 'none';
    document.documentElement.style.overflow = '';
    document.body.style.overflow = '';
  }
  function goNextWord() {
    hideModal();
    if (idx < words.length - 1) { idx++; render(); }
  }

  // ---------- lang buttons ----------
  function updateLangButtons(){
    $all('.lang-switch .lang-btn').forEach(b => {
      const lang = b.dataset.lang || '';
      const active = (learningLanguage === '' && lang === '') ||
                     (learningLanguage !== '' && lang === learningLanguage);
      b.classList.toggle('active', active);
    });
  }
  $all('.lang-switch .lang-btn').forEach(b => {
    b.addEventListener('click', () => {
      learningLanguage = b.dataset.lang || ''; // '' = Все
      updateLangButtons();
      render();
    });
  });

  // ---------- controls ----------
  if (undoBtn)  undoBtn.addEventListener('click', undo);
  if (clearBtn) clearBtn.addEventListener('click', clearAll);
  if (checkBtn) checkBtn.addEventListener('click', check);
  if (prevBtn)  prevBtn.addEventListener('click', () => { hideModal(); if (idx > 0) { idx--; render(); }});
  if (nextBtn)  nextBtn.addEventListener('click', () => { hideModal(); if (idx < words.length - 1) { idx++; render(); }});

  // Модалка
  if (modalClose) modalClose.addEventListener('click', hideModal);
  if (resultModal) {
    resultModal.addEventListener('click', (e)=>{ if (e.target === resultModal) hideModal(); });
  }
  if (nextWordBtn) nextWordBtn.addEventListener('click', goNextWord);
  document.addEventListener('keydown', (e)=>{
    if (!resultModal) return;
    const opened = resultModal.classList.contains('show');
    if (opened && e.key === 'Escape') hideModal();
    if (opened && (e.key === 'Enter' || e.key === 'ArrowRight')) goNextWord();
  });

  // [ДОБАВЛЕНО v7.5] обработчик чекбокса «сложное»
  if (diffToggle) {
    diffToggle.addEventListener('change', async () => {
      const w = words[idx];
      if (!w || typeof w.id === 'undefined') return;
      try {
        await api('/api/difficult/set', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({ id: w.id, difficult: diffToggle.checked ? 1 : 0 })
        });
        // локально тоже отметим
        w.difficult = diffToggle.checked ? 1 : 0;
      } catch(e) {}
    });
  }
})();
