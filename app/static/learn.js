(function () {
  // помечаем, что скрипт успешно стартовал (для fallback в learn.html)
  window.__LEARN_BOOTED__ = true;

  // ---------- helpers ----------
  function $(sel, root = document) { return root.querySelector(sel); }
  function $all(sel, root = document) { return Array.from(root.querySelectorAll(sel)); }
  function audioPlay(src) { if (!src) return; new Audio(src).play().catch(()=>{}); }

  // ---------- корневые элементы ----------
  const root = document.getElementById('learn-root');
  if (!root) {
    console.error('[learn] #learn-root не найден — проверь learn.html');
    return;
  }

  // подстраховка: берём название урока из data / глобалки / query
  function _lessonFromQuery() {
    try { return new URLSearchParams(location.search).get('lesson') || ''; }
    catch(e){ return ''; }
  }
  const lessonTitle =
    (root.dataset && root.dataset.lesson ? root.dataset.lesson : '') ||
    (typeof window.LESSON_TITLE !== 'undefined' ? window.LESSON_TITLE : '') ||
    _lessonFromQuery();

  if (!lessonTitle) {
    console.error('[learn] lessonTitle пуст — не смогу загрузить слова');
    return;
  }
  console.log('[learn] lessonTitle =', lessonTitle);

  // элементы интерфейса
  const wordView    = $('#word-view');
  const lettersPool = $('#letters-pool');
  const answerSlots = $('#answer-slots');
  const progress    = $('#progress');
  const undoBtn     = $('#undo-btn');
  const clearBtn    = $('#clear-btn');
  const checkBtn    = $('#check-btn');
  const prevBtn     = $('#prev-btn');
  const nextBtn     = $('#next-btn');
  const resultModal = $('#result-modal');
  const modalClose  = $('#modal-close');
  const nextWordBtn = $('#next-word-btn');
  const modalLine1  = $('#modal-line1');
  const modalLine2  = $('#modal-line2');
  const modalLine3  = $('#modal-line3');

  // состояние
  let learningLanguage = ''; // '', 'nl', 'en', 'ru'
  let words = [];
  let idx = 0;
  let picked = []; // [{ch, fromIndex}]

  // ---------- загрузка слов ----------
  const apiUrl = `/api/lesson_words?lesson=${encodeURIComponent(lessonTitle)}`;
  console.log('[learn] fetch:', apiUrl);

  fetch(apiUrl)
    .then(r => r.json())
    .then(data => {
      if (!data || data.ok === false) {
        console.error('[learn] API error:', data && data.error);
        if (wordView) wordView.textContent = 'Ошибка загрузки слов.';
        return;
      }
      words = data.items || [];
      if (!Array.isArray(words) || !words.length) {
        if (wordView) wordView.textContent = 'В этом уроке пока нет слов.';
        return;
      }
      render();
    })
    .catch(err => {
      console.error('[learn] fetch failed:', err);
      if (wordView) wordView.textContent = 'Ошибка сети при загрузке слов.';
    });

  // ---------- отрисовка ----------
  function render() {
    const w = words[idx];
    if (progress) progress.textContent = `${idx + 1} / ${words.length}`;

    const lines = [];
    lines.push(block('en', w.word_en,        w.sentence_en, w.audio_en));
    lines.push(block('ru', w.translation_ru, w.sentence_ru, w.audio_ru));
    lines.push(block('nl', w.translation_nl, w.sentence_nl, w.audio_nl));
    if (wordView) wordView.innerHTML = lines.join('');

    const target = pickTargetWord(w);
    buildLetters(target);
    buildSlots(target.length);

    if (prevBtn) prevBtn.disabled = (idx === 0);
    if (nextBtn) nextBtn.disabled = (idx === words.length - 1);
  }

  function block(lang, word, sentence, audio) {
    const label = ({en:'(en)', ru:'(ru)', nl:'(nl)'}[lang]) || '';
    const badge = `<span class="badge">${label}</span>`;
    const play  = `<button class="btn" onclick="(${audioPlay.toString()})('${audio||''}')">▶</button>`;
    return `
      <div class="word-block">
        <div class="word-title">${badge} <strong>${escapeHtml(word||'')}</strong> ${play}</div>
        <div class="word-sentence">${escapeHtml(sentence||'')}</div>
      </div>
    `;
  }

  function pickTargetWord(w) {
    if (learningLanguage === 'en') return w.word_en || '';
    if (learningLanguage === 'ru') return w.translation_ru || '';
    if (learningLanguage === 'nl') return w.translation_nl || '';
    return w.translation_nl || '';
  }

  function buildLetters(target) {
    picked = [];
    if (lettersPool) lettersPool.innerHTML = '';
    target = target || '';
    const chars = target.split('');
    if (chars.length < 6) chars.push(...randNoises(6 - chars.length));
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

  function check() {
    const w = words[idx];
    const target = pickTargetWord(w);
    const user = (answerSlots ? Array.from(answerSlots.querySelectorAll('.slot')) : [])
                   .map(s=>s.textContent||'').join('');
    const ok = (user.toLowerCase() === (target||'').toLowerCase());
    if (ok) {
      showModal('<strong>Правильно!</strong>', `Слово: <strong>${escapeHtml(target)}</strong>`, 'Отличная работа!', wAudio(w));
    } else {
      showModal('<strong>Неправильно!</strong>', `Правильно: <strong>${escapeHtml(target)}</strong>`, escapeHtml(pickSentence(w)), wAudio(w));
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
    if (modalLine1) modalLine1.innerHTML = line1;
    if (modalLine2) modalLine2.innerHTML = `${line2} ${audioSrc ? `<button class="btn" onclick="(${audioPlay.toString()})('${audioSrc}')">▶</button>` : ''}`;
    if (modalLine3) modalLine3.textContent = line3;
    resultModal.style.display = 'flex';
  }

  // ---------- события ----------
  if (undoBtn)    undoBtn.addEventListener('click', undo);
  if (clearBtn)   clearBtn.addEventListener('click', clearAll);
  if (checkBtn)   checkBtn.addEventListener('click', check);
  if (prevBtn)    prevBtn.addEventListener('click', () => { if (idx > 0) { idx--; render(); }});
  if (nextBtn)    nextBtn.addEventListener('click', () => { if (idx < words.length - 1) { idx++; render(); }});
  if (modalClose) modalClose.addEventListener('click', () => { if (resultModal) resultModal.style.display = 'none'; });
  if (nextWordBtn) nextWordBtn.addEventListener('click', () => {
    if (resultModal) resultModal.style.display = 'none';
    if (idx < words.length - 1) { idx++; render(); }
  });
  $all('.lang-switch .btn').forEach(b => {
    b.addEventListener('click', () => { learningLanguage = b.dataset.lang || ''; render(); });
  });

  // ---------- утилиты ----------
  function shuffle(a){ for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];} }
  function randNoises(n){ const letters='aeiourtnsl'; const out=[]; while(out.length<n){ out.push(letters[Math.floor(Math.random()*letters.length)]);} return out; }
  function escapeHtml(s){ return (s||'').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])); }

})();
