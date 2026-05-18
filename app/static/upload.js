// upload.js — страница загрузки слов с генерацией через Ollama

let lessonCounter = 0;
let pendingDuplicateDelete = null;

function _esc(s) {
  if (s == null) return '';
  if (Array.isArray(s)) s = s[0] ?? '';
  if (typeof s !== 'string') s = String(s);
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function _jsArg(s) {
  if (s == null) return "''";
  if (Array.isArray(s)) s = s[0] ?? '';
  return JSON.stringify(String(s)).replace(/</g, '\\u003c');
}

async function initAdminSubscriptionsLink() {
  const link = document.getElementById('admin-subscriptions-link');
  if (!link) return;
  try {
    const resp = await apiFetch('/api/me');
    const data = await resp.json();
    if (!data.ok || !data.is_admin) return;
    link.href = '/admin/users';
    link.style.display = 'inline-flex';
  } catch (_) {}
}

function addLesson() {
  const idx = lessonCounter++;
  const container = document.getElementById('lessons-container');
  const div = document.createElement('div');
  div.className = 'lesson-block';
  div.id = `lesson-block-${idx}`;
  div.innerHTML = `
    <div class="lesson-head">
      <span class="lesson-num">Урок</span>
      <div class="lesson-row" style="flex:1;flex-wrap:nowrap;gap:8px">
        <input type="text" class="lesson-name" placeholder="Название урока (например: Het huis)" style="flex:1">
        <select class="lesson-lang">
          <option value="nl">NL → EN/RU</option>
          <option value="en">EN → NL/RU</option>
        </select>
      </div>
      <button type="button" class="del-row-btn remove-lesson-btn" onclick="removeLesson(${idx})" title="Удалить урок">✕</button>
    </div>
    <div class="lesson-fields">
      <textarea class="words-ta" placeholder="Формат 1 — одно NL слово в строке:&#10;het huis&#10;de kamer&#10;&#10;Формат 2 — пары NL + RU (с пустой строкой между):&#10;bewegen&#10;двигаться&#10;&#10;Start&#9;de kamer&#9;&#10;комната"></textarea>
      <p class="lesson-hint">Формат определяется автоматически: если есть русский текст — NL+RU, иначе — только NL слова</p>
    </div>
    <div class="lesson-gen-status" id="lgs-${idx}"></div>
    <div class="regen-row" id="regen-row-${idx}" style="display:none;margin-top:6px">
      <button type="button" class="ghost-btn regen-lesson-btn" style="font-size:12px;padding:4px 12px"
        onclick="regenerateLesson(${idx})">🔄 Перегенерировать урок</button>
      <span class="regen-hint" style="font-size:11px;color:#94a3b8;margin-left:8px">
        Перегенерирует все слова с текущим уровнем и исправлениями
      </span>
    </div>
  `;
  container.appendChild(div);
  _updateRemoveButtons();
}

function removeLesson(idx) {
  const el = document.getElementById(`lesson-block-${idx}`);
  if (el) el.remove();
  _updateRemoveButtons();
}

function _updateRemoveButtons() {
  const btns = document.querySelectorAll('.remove-lesson-btn');
  btns.forEach(b => { b.style.visibility = btns.length > 1 ? 'visible' : 'hidden'; });
}

// ── Ollama helpers ──────────────────────────────────────────────

function _ollamaUrl() {
  return (document.getElementById('ollama-url').value || 'http://localhost:11434').replace(/\/$/, '');
}
function _ollamaModel() {
  return document.getElementById('ollama-model').value.trim() || 'llama3.1:8b';
}

async function checkOllama() {
  const statusEl = document.getElementById('ollama-status');
  statusEl.textContent = '⏳ Проверка...';
  statusEl.className = 'ollama-status';
  try {
    const r = await fetch(_ollamaUrl() + '/api/tags', { signal: AbortSignal.timeout(5000) });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    const models = (data.models || []).map(m => m.name).join(', ');
    statusEl.textContent = `✅ Работает. Модели: ${models || '(нет)'}`;
    statusEl.className = 'ollama-status ok';
  } catch(e) {
    statusEl.textContent = `❌ Недоступна: ${e.message}. Запустите Ollama на компьютере.`;
    statusEl.className = 'ollama-status err';
  }
}

function _cefrLevel() {
  return (document.getElementById('cefr-level')?.value || 'A2');
}

function _buildPrompt(lessonName, words, lang, level) {
  const langLabel = lang === 'nl' ? 'Dutch' : 'English';
  const wordList  = words.map((w, i) => `${i+1}. ${w}`).join('\n');
  return `You are a language learning assistant. Create vocabulary entries for a language course.
Lesson: "${lessonName}"
Input language: ${langLabel}
CEFR level for example sentences: ${level || 'A2'}
Words:
${wordList}

For each word return a JSON object with exactly these keys:
- "nl": Dutch word with article if noun (e.g. "de rekening", "het huis")
- "en": natural English translation (1-3 words)
- "ru": natural Russian translation — use proper literary Russian, NOT word-for-word translation. For example: "de rekening" → "счёт", "betalen" → "платить". The Russian must sound like a native speaker wrote it.
- "ex_nl": one short example sentence in Dutch (${level || 'A2'} level vocabulary and grammar). Surround the studied word (or its inflected form) with ** markers, e.g. "Ik moet de **rekening** betalen."
- "ex_en": the same sentence translated naturally into English. Surround the corresponding word with ** markers, e.g. "I need to pay the **bill**."
- "ex_ru": the same sentence translated naturally into Russian. Surround the corresponding word with ** markers, e.g. "Мне нужно оплатить **счёт**."
- The value of "en" must be the base/dictionary form of the word marked with ** in "ex_en"
- The value of "ru" must be the base/dictionary form of the word marked with ** in "ex_ru"

Return ONLY a JSON array with one object per word. No markdown, no code fences, no explanation.`;
}

async function _callOllama(lessonName, words, lang, level) {
  const body = {
    model:   _ollamaModel(),
    messages: [
      { role: 'system', content: 'You are a language assistant. Return ONLY valid JSON arrays, no markdown fences, no explanations.' },
      { role: 'user',   content: _buildPrompt(lessonName, words, lang, level) }
    ],
    stream: false,
    format: 'json'
  };

  const resp = await fetch(_ollamaUrl() + '/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(120000)
  });
  if (!resp.ok) throw new Error(`Ollama HTTP ${resp.status}`);

  const data = await resp.json();
  const raw = (data.message?.content || data.response || '').trim();

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch(_) {
    // Try to extract JSON array from text
    const m = raw.match(/\[[\s\S]*\]/);
    if (m) parsed = JSON.parse(m[0]);
    else throw new Error('Не удалось разобрать ответ Ollama как JSON');
  }

  // Unwrap if object wrapping an array
  if (!Array.isArray(parsed)) {
    const keys = Object.keys(parsed);
    if (keys.length === 1 && Array.isArray(parsed[keys[0]])) {
      parsed = parsed[keys[0]];
    } else {
      // Might be a single word object — wrap it
      parsed = [parsed];
    }
  }
  return parsed;
}

// ── Detect input format ──────────────────────────────────────────
// Returns 'nl+ru' if Cyrillic found, else 'nl'
function _detectFormat(text) {
  return /[а-яёА-ЯЁ]/.test(text) ? 'nl+ru' : 'nl';
}

// ── Main generate ───────────────────────────────────────────────

async function generateWords() {
  const blocks   = document.querySelectorAll('.lesson-block');
  const genBtn   = document.getElementById('generate-btn');
  const statusEl = document.getElementById('gen-status');

  genBtn.disabled = true;

  const tbody   = document.getElementById('preview-body');
  const section = document.getElementById('preview-section');
  tbody.innerHTML = '';
  section.style.display = '';
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });

  const level = _cefrLevel();
  let totalDone = 0, totalWords = 0;

  // Pre-parse all blocks to count total and detect formats
  const parsedBlocks = [];
  blocks.forEach(block => {
    const rawText    = block.querySelector('.words-ta').value;
    const fmt        = _detectFormat(rawText);
    const rawWords   = fmt === 'nl+ru'
      ? parsePasteText(rawText)
      : rawText.split('\n').map(w => w.trim()).filter(Boolean).map(w => ({ nl: w, ru: null }));
    const { unique: words, dupes } = _deduplicateWords(rawWords);
    totalWords += words.length;
    parsedBlocks.push({
      block, words, dupes, fmt,
      lessonName: block.querySelector('.lesson-name').value.trim(),
      lang:       block.querySelector('.lesson-lang').value,
    });
  });

  if (!totalWords) {
    statusEl.textContent = '⚠ Нет слов. Заполните хотя бы один урок.';
    genBtn.disabled = false;
    return;
  }

  for (const { block, words, dupes, fmt, lessonName, lang } of parsedBlocks) {
    const lgs = block.querySelector('[id^="lgs-"]');

    if (!lessonName || !words.length) {
      if (lgs) lgs.textContent = '⚠ Заполните название урока и слова';
      continue;
    }

    if (dupes.length && lgs) {
      lgs.textContent = `⚠ Пропущено ${dupes.length} дубл${dupes.length === 1 ? 'ь' : 'я/ей'}: ${dupes.join(', ')}`;
    }

    let doneInBlock = 0;

    for (const wordObj of words) {
      const wordLabel = wordObj.nl;
      totalDone++;
      doneInBlock++;
      statusEl.textContent = `⏳ ${totalDone}/${totalWords}: «${wordLabel}» (${lessonName})`;
      if (lgs) lgs.textContent = `⏳ ${doneInBlock}/${words.length}: ${wordLabel}`;

      const placeholder = _addPendingRow(lessonName, wordLabel);

      try {
        let item;
        if (fmt === 'nl+ru') {
          // NL + RU known → Ollama generates only EN + sentences
          const items = await _callOllamaRuKnown(lessonName, wordObj.nl, wordObj.ru || '', level);
          item = Array.isArray(items) ? items[0] : items;
        } else {
          // Only NL → Ollama generates EN, RU + sentences
          const items = await _callOllama(lessonName, [wordLabel], lang, level);
          item = Array.isArray(items) ? items[0] : items;
        }
        if (!item) throw new Error('Ollama вернула пустой ответ');
        _fillRow(placeholder, {
          lesson: lessonName, word: wordLabel,
          nl:    item.nl    || wordObj.nl  || '',
          en:    item.en    || '',
          ru:    item.ru    || wordObj.ru  || '',
          ex_nl: item.ex_nl || '', ex_en: item.ex_en || '', ex_ru: item.ex_ru || '',
        }, lang, level, wordObj.ru || null);
      } catch(e) {
        _markRowError(placeholder, wordLabel, e);
      }
    }

    if (lgs) lgs.textContent = `✅ ${words.length} слов обработано`;
    const regenRow = block.querySelector('[id^="regen-row-"]');
    if (regenRow) regenRow.style.display = '';
  }

  statusEl.textContent = `✅ Готово: ${totalDone} слов`;
  genBtn.disabled = false;
}

// ── Pending placeholder row ──────────────────────────────────────
function _addPendingRow(lesson, word) {
  const tbody = document.getElementById('preview-body');
  const tr    = document.createElement('tr');
  tr.style.opacity = '0.5';
  tr.innerHTML = `
    <td class="cell-lesson" contenteditable="true">${_esc(lesson)}</td>
    <td class="cell-nl"     contenteditable="true" colspan="6" style="color:#64748b;font-style:italic">⏳ ${_esc(word)} — генерирую…</td>
    <td></td>
  `;
  tbody.appendChild(tr);
  return tr;
}

// ── Fill row with generated data ─────────────────────────────────
// knownRu: if set, the RU translation was user-supplied (not AI) — stored for smart re-gen
function _fillRow(tr, row, lang, level, knownRu) {
  tr.style.opacity = '';
  tr.dataset.word   = row.word || '';
  tr.dataset.lesson = row.lesson || '';
  tr.dataset.lang   = lang || 'nl';
  tr.dataset.level  = level || 'A2';
  if (knownRu != null) tr.dataset.knownRu = knownRu;
  tr.innerHTML = `
    <td class="cell-lesson" contenteditable="true">${_esc(row.lesson)}</td>
    <td class="cell-nl"     contenteditable="true">${_esc(row.nl)}</td>
    <td class="cell-en"     contenteditable="true">${_esc(row.en)}</td>
    <td class="cell-ru"     contenteditable="true">${_esc(row.ru)}</td>
    <td class="cell-ex-nl"  contenteditable="true">${_esc(row.ex_nl)}</td>
    <td class="cell-ex-en"  contenteditable="true">${_esc(row.ex_en)}</td>
    <td class="cell-ex-ru"  contenteditable="true">${_esc(row.ex_ru)}</td>
    <td style="white-space:nowrap">
      <button type="button" class="refresh-row-btn" onclick="refreshRow(this)" title="Перегенерировать">🔄</button>
      <button type="button" class="del-row-btn"     onclick="this.closest('tr').remove()" title="Удалить">✕</button>
    </td>
  `;
}

// ── Mark row as error ────────────────────────────────────────────
function _markRowError(tr, word, err) {
  tr.style.opacity = '';
  tr.style.background = '#fff1f2';
  const lesson = tr.querySelector('.cell-lesson')?.textContent || '';

  let msg = '';
  if (err instanceof Error) {
    // Translate common technical errors into human-readable text
    const raw = err.message || '';
    if (raw.includes('replace is not a function') || raw.includes('is not a string')) {
      msg = `Ollama вернула данные в неверном формате для «${word}» — нажмите 🔄 для повтора`;
    } else if (raw.includes('Failed to fetch') || raw.includes('NetworkError')) {
      msg = 'Ollama недоступна — проверьте, что она запущена';
    } else if (raw.includes('timeout') || raw.includes('AbortError')) {
      msg = `Время ожидания истекло для «${word}» — нажмите 🔄`;
    } else if (raw.includes('JSON') || raw.includes('разобрать')) {
      msg = `Не удалось разобрать ответ Ollama для «${word}» — нажмите 🔄`;
    } else {
      msg = raw || 'Неизвестная ошибка';
    }
  } else {
    msg = String(err);
  }

  tr.innerHTML = `
    <td class="cell-lesson" contenteditable="true">${_esc(lesson)}</td>
    <td colspan="6" style="color:#dc2626;font-size:12px" title="${_esc(err?.message || '')}">❌ ${_esc(msg)}</td>
    <td style="white-space:nowrap">
      <button type="button" class="refresh-row-btn" onclick="refreshRow(this)" title="Повторить">🔄</button>
      <button type="button" class="del-row-btn"     onclick="this.closest('tr').remove()" title="Удалить">✕</button>
    </td>
  `;
}

// ── Regenerate single row ────────────────────────────────────────
async function refreshRow(btn) {
  const tr      = btn.closest('tr');
  const word    = tr.dataset.word;
  const lesson  = tr.dataset.lesson || tr.querySelector('.cell-lesson')?.textContent?.trim() || '';
  const lang    = tr.dataset.lang   || 'nl';
  const level   = tr.dataset.level  || _cefrLevel();
  const knownRu = tr.dataset.knownRu != null ? tr.dataset.knownRu : null;

  if (!word || !lesson) return;

  btn.textContent  = '⏳';
  btn.disabled     = true;
  tr.style.opacity = '0.5';

  try {
    let item;
    if (knownRu != null) {
      // RU was user-supplied — preserve it, only regenerate EN + sentences
      const items = await _callOllamaRuKnown(lesson, word, knownRu, level);
      item = Array.isArray(items) ? items[0] : items;
    } else {
      const items = await _callOllama(lesson, [word], lang, level);
      item = Array.isArray(items) ? items[0] : items;
    }
    if (!item) throw new Error('Ollama вернула пустой ответ');
    _fillRow(tr, {
      lesson, word,
      nl:    item.nl    || '', en:    item.en    || '', ru:    item.ru    || '',
      ex_nl: item.ex_nl || '', ex_en: item.ex_en || '', ex_ru: item.ex_ru || '',
    }, lang, level, knownRu);
  } catch(e) {
    _markRowError(tr, word, e);
    tr.dataset.word   = word;
    tr.dataset.lesson = lesson;
    tr.dataset.lang   = lang;
    tr.dataset.level  = level;
    if (knownRu != null) tr.dataset.knownRu = knownRu;
  }
}

// ── Regenerate all words in a lesson block ──────────────────────
async function regenerateLesson(idx) {
  const block = document.getElementById(`lesson-block-${idx}`);
  if (!block) return;

  const lessonName = block.querySelector('.lesson-name').value.trim();
  const lang       = block.querySelector('.lesson-lang').value;
  const level      = _cefrLevel();

  if (!lessonName) {
    alert('Введите название урока');
    return;
  }

  // Find all preview rows belonging to this lesson
  const rows = Array.from(document.querySelectorAll('#preview-body tr')).filter(tr => {
    const cell = tr.querySelector('.cell-lesson');
    return (tr.dataset.lesson === lessonName) || (cell && cell.textContent.trim() === lessonName);
  });

  if (!rows.length) {
    alert('Нет сгенерированных строк для этого урока. Сначала нажмите «Сгенерировать переводы».');
    return;
  }

  const btn = block.querySelector('.regen-lesson-btn');
  const lgs = block.querySelector('[id^="lgs-"]');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ Перегенерирую…'; }

  let done = 0;
  for (const tr of rows) {
    // use original word from dataset; fall back to current NL cell text
    const word = tr.dataset.word || tr.querySelector('.cell-nl')?.textContent?.trim() || '';
    if (!word) continue;

    done++;
    if (lgs) lgs.textContent = `⏳ ${done}/${rows.length}: «${word}» (уровень ${level})`;
    tr.style.opacity = '0.5';

    try {
      const items = await _callOllama(lessonName, [word], lang, level);
      const item  = Array.isArray(items) ? items[0] : items;
      if (!item) throw new Error('Пустой ответ');
      _fillRow(tr, {
        lesson: lessonName, word,
        nl:    item.nl    || '', en:    item.en    || '', ru:    item.ru    || '',
        ex_nl: item.ex_nl || '', ex_en: item.ex_en || '', ex_ru: item.ex_ru || '',
      }, lang, level);
    } catch(e) {
      _markRowError(tr, word, e);
      tr.dataset.word   = word;
      tr.dataset.lesson = lessonName;
      tr.dataset.lang   = lang;
      tr.dataset.level  = level;
    }
  }

  if (lgs) lgs.textContent = `✅ Перегенерировано ${done} слов (уровень ${level})`;
  if (btn) { btn.disabled = false; btn.textContent = '🔄 Перегенерировать урок'; }
}

// ── Preview table (legacy, kept for _buildTable callers) ─────────
function _buildTable(rows) {
  const tbody = document.getElementById('preview-body');
  tbody.innerHTML = '';
  rows.forEach(row => _fillRow(document.createElement('tr'), row, row.lang || 'nl'));
  const section = document.getElementById('preview-section');
  section.style.display = '';
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── Import to DB ────────────────────────────────────────────────

function _getTableData() {
  const rows = [];
  document.querySelectorAll('#preview-body tr').forEach(tr => {
    rows.push({
      lesson: tr.querySelector('.cell-lesson').textContent.trim(),
      nl:     tr.querySelector('.cell-nl').textContent.trim(),
      en:     tr.querySelector('.cell-en').textContent.trim(),
      ru:     tr.querySelector('.cell-ru').textContent.trim(),
      ex_nl:  tr.querySelector('.cell-ex-nl').textContent.trim(),
      ex_en:  tr.querySelector('.cell-ex-en').textContent.trim(),
      ex_ru:  tr.querySelector('.cell-ex-ru').textContent.trim(),
    });
  });
  return rows;
}

function _groupByLesson(rows) {
  const map = new Map();
  rows.forEach(row => {
    const l = row.lesson || 'Без урока';
    if (!map.has(l)) map.set(l, []);
    map.get(l).push(row);
  });
  return Array.from(map.entries()).map(([lesson, words]) => ({ lesson, words }));
}

async function importWords() {
  const uploadBtn = document.getElementById('upload-btn');
  const statusEl  = document.getElementById('upload-status');
  const rows      = _getTableData();

  if (!rows.length) { statusEl.textContent = 'Таблица пуста'; return; }

  uploadBtn.disabled = true;
  statusEl.textContent = '⏳ Загружаю в базу данных...';

  try {
    const lessons = _groupByLesson(rows);
    const resp = await apiFetch('/api/import-words', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lessons })
    });
    const data = await resp.json();

    if (data.ok) {
      statusEl.innerHTML = `✅ Загружено <strong>${data.count}</strong> слов! `
        + `<a href="/">← Посмотреть все уроки</a>`;
      document.getElementById('preview-section').style.display = 'none';
      // Clear lesson blocks
      document.querySelectorAll('.words-ta').forEach(ta => { ta.value = ''; });
      document.querySelectorAll('.lesson-gen-status').forEach(el => { el.textContent = ''; });
      _shareLessonsLoaded = false;
    } else {
      statusEl.textContent = `❌ Ошибка: ${data.error || 'неизвестная ошибка'}`;
    }
  } catch(e) {
    statusEl.textContent = `❌ Ошибка: ${e.message}`;
  }

  uploadBtn.disabled = false;
}

// ════════════════════════════════════════════════════════════════
//  PASTE TAB  (NL + RU format from Ollama / Telegram)
// ════════════════════════════════════════════════════════════════

function parsePasteText(text) {
  const words = [];
  const lines = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
  let i = 0;
  while (i < lines.length) {
    // skip empty lines
    while (i < lines.length && !lines[i].trim()) i++;
    if (i >= lines.length) break;

    // NL line: strip leading "Start" + tabs/spaces, strip trailing tabs
    let nlLine = lines[i];
    nlLine = nlLine.replace(/^Start[\t ]*/i, '').replace(/[\t ]+$/, '').trim();
    i++;

    // find RU line (next non-empty)
    while (i < lines.length && !lines[i].trim()) i++;
    if (i >= lines.length) break;

    const ruLine = lines[i].trim();
    i++;

    if (nlLine && ruLine) words.push({ nl: nlLine, ru: ruLine });
  }
  return words;
}


async function _callOllamaRuKnown(lessonName, nl, ru, level) {
  const prompt = `You are a language learning assistant for a Dutch course.
Lesson: "${lessonName}"
CEFR level: ${level || 'A2'}

Dutch word: "${nl}"
Russian translation (already known): "${ru}"

Provide the missing fields. Return a JSON array with ONE object:
- "nl": "${nl}" (copy exactly)
- "ru": "${ru}" (copy exactly)
- "en": natural English translation (1-3 words)
- "ex_nl": one short Dutch example sentence (${level || 'A2'} level). Surround the studied word (or its inflected form) with ** markers, e.g. "Ik moet de **rekening** betalen."
- "ex_en": that sentence in English. Surround the corresponding word with ** markers, e.g. "I need to pay the **bill**."
- "ex_ru": that sentence in Russian. Surround the corresponding word with ** markers, e.g. "Мне нужно оплатить **счёт**."
- The value of "en" must be the base/dictionary form of the word marked with ** in "ex_en"
- The value of "ru" must be the base/dictionary form of the word marked with ** in "ex_ru"

Return ONLY a JSON array. No markdown, no fences, no explanation.`;

  const body = {
    model:   _ollamaModel(),
    messages: [
      { role: 'system', content: 'Return ONLY valid JSON arrays, no markdown.' },
      { role: 'user',   content: prompt }
    ],
    stream: false,
    format: 'json'
  };

  const resp = await fetch(_ollamaUrl() + '/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(60000)
  });
  if (!resp.ok) throw new Error(`Ollama HTTP ${resp.status}`);

  const data = await resp.json();
  const raw  = (data.message?.content || data.response || '').trim();

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch(_) {
    const m = raw.match(/\[[\s\S]*\]/);
    if (m) parsed = JSON.parse(m[0]);
    else throw new Error('Не удалось разобрать ответ Ollama');
  }
  if (!Array.isArray(parsed)) {
    const keys = Object.keys(parsed);
    if (keys.length === 1 && Array.isArray(parsed[keys[0]])) parsed = parsed[keys[0]];
    else parsed = [parsed];
  }
  return parsed;
}

addLesson();
initAdminSubscriptionsLink();

// ════════════════════════════════════════════════════════════════
//  TOPIC GENERATOR TAB
// ════════════════════════════════════════════════════════════════

function _topicOllamaUrl() {
  const el = document.getElementById('topic-ollama-url');
  return (el ? el.value : document.getElementById('ollama-url').value || 'http://localhost:11434').replace(/\/$/, '');
}
function _topicOllamaModel() {
  const el = document.getElementById('topic-ollama-model');
  return (el ? el.value : document.getElementById('ollama-model').value || 'llama3.1:8b').trim();
}

async function checkOllamaTopic() {
  const statusEl = document.getElementById('topic-ollama-status');
  statusEl.textContent = '⏳ Проверка...';
  statusEl.className = 'ollama-status';
  try {
    const r = await fetch(_topicOllamaUrl() + '/api/tags', { signal: AbortSignal.timeout(5000) });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    const models = (data.models || []).map(m => m.name).join(', ');
    statusEl.textContent = `✅ Работает. Модели: ${models || '(нет)'}`;
    statusEl.className = 'ollama-status ok';
  } catch(e) {
    statusEl.textContent = `❌ Недоступна: ${e.message}`;
    statusEl.className = 'ollama-status err';
  }
}

async function _fetchExistingNlWords() {
  try {
    const resp = await apiFetch('/api/words/nl-list');
    const data = await resp.json();
    return data.ok ? (data.words || []) : [];
  } catch(e) {
    return [];
  }
}

function _stripArticle(w) {
  return w.toLowerCase().trim().replace(/^(de|het|een)\s+/i, '').trim();
}

function _deduplicateWords(words) {
  const seen = new Set();
  const dupes = [];
  const unique = words.filter(wordObj => {
    const base = (wordObj.nl || '').toLowerCase().trim()
      .replace(/^(de|het|een|the|a|an)\s+/i, '').trim();
    if (!base) return true;
    if (seen.has(base)) { dupes.push(wordObj.nl); return false; }
    seen.add(base);
    return true;
  });
  return { unique, dupes };
}

async function _suggestWordsByTopic(topic, lang, level, count, existingWords) {
  const langLabel = lang === 'nl' ? 'Dutch' : 'English';
  const avoid = existingWords.length
    ? `\nDo NOT suggest any of these words (already in the user's vocabulary): ${existingWords.slice(0, 150).join(', ')}`
    : '';

  const prompt = `You are a language learning assistant.
Topic: "${topic}"
Language: ${langLabel}
CEFR level: ${level}
${avoid}

Suggest exactly ${count} ${langLabel} words or short phrases that are:
- Relevant to the topic "${topic}"
- Appropriate for ${level} level learners
- Not repeating any words already listed above
- Include articles (de/het) for Dutch nouns

Return ONLY a JSON array of strings. No explanation, no markdown.
Example: ["de appel", "eten", "lekker", "het restaurant", "betalen"]`;

  const body = {
    model:   _topicOllamaModel(),
    messages: [
      { role: 'system', content: 'Return ONLY a valid JSON array of strings. No markdown, no explanation.' },
      { role: 'user',   content: prompt }
    ],
    stream: false,
    format: 'json'
  };

  const resp = await fetch(_topicOllamaUrl() + '/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(60000)
  });
  if (!resp.ok) throw new Error(`Ollama HTTP ${resp.status}`);

  const data = await resp.json();
  const raw  = (data.message?.content || data.response || '').trim();

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch(_) {
    const m = raw.match(/\[[\s\S]*\]/);
    if (m) parsed = JSON.parse(m[0]);
    else throw new Error('Не удалось разобрать ответ Ollama как JSON');
  }

  if (!Array.isArray(parsed)) {
    // Maybe it's {words: [...]} or similar
    const vals = Object.values(parsed);
    parsed = vals.flat().filter(v => typeof v === 'string');
  }

  return parsed.filter(w => typeof w === 'string' && w.trim());
}

async function generateByTopic() {
  const topic      = (document.getElementById('topic-input').value || '').trim();
  const lessonName = (document.getElementById('topic-lesson-name').value || '').trim() || topic;
  const level      = document.getElementById('topic-level').value;
  const lang       = document.getElementById('topic-lang').value;
  const count      = parseInt(document.getElementById('topic-count').value, 10) || 15;
  const statusEl   = document.getElementById('topic-status');
  const dedupEl    = document.getElementById('topic-dedup-info');
  const genBtn     = document.getElementById('topic-gen-btn');

  if (!topic) { statusEl.textContent = '⚠ Введите тему'; return; }

  genBtn.disabled  = true;
  dedupEl.style.display = 'none';
  statusEl.textContent  = '⏳ Загружаю слова из базы данных…';

  // Step 1: get existing words for deduplication
  const existingWords = await _fetchExistingNlWords();
  const existingSet   = new Set(existingWords);                       // exact lowercase
  const existingBase  = new Set(existingWords.map(_stripArticle));    // without article

  // Step 2: ask Ollama for word suggestions
  statusEl.textContent = `⏳ Запрашиваю ${count} слов по теме «${topic}» у Ollama…`;
  let suggested;
  try {
    suggested = await _suggestWordsByTopic(topic, lang, level, count, existingWords);
  } catch(e) {
    statusEl.textContent = `❌ Ошибка Ollama: ${e.message}`;
    genBtn.disabled = false;
    return;
  }

  // Step 3: filter duplicates
  const newWords = suggested.filter(w => {
    const low  = w.toLowerCase().trim();
    const base = _stripArticle(w);
    return !existingSet.has(low) && !existingBase.has(base);
  });

  const skipped = suggested.length - newWords.length;

  if (skipped > 0) {
    dedupEl.textContent   = `ℹ️ Пропущено ${skipped} слов — уже есть в базе данных (из ${suggested.length} предложенных)`;
    dedupEl.style.display = '';
  }

  if (!newWords.length) {
    statusEl.textContent = `⚠ Все предложенные слова (${suggested.length}) уже есть в базе. Попробуйте другую тему или уровень.`;
    genBtn.disabled = false;
    return;
  }

  // Step 4: generate full entries word by word
  const tbody   = document.getElementById('preview-body');
  const section = document.getElementById('preview-section');
  section.style.display = '';
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });

  let done = 0;
  for (const word of newWords) {
    done++;
    statusEl.textContent = `⏳ ${done}/${newWords.length}: «${word}» — генерирую перевод и примеры…`;

    const placeholder = _addPendingRow(lessonName, word);

    try {
      const items = await _callOllamaForTopic(lessonName, word, lang, level);
      const item  = Array.isArray(items) ? items[0] : items;
      if (!item) throw new Error('Ollama вернула пустой ответ');
      _fillRow(placeholder, {
        lesson: lessonName, word,
        nl:    item.nl    || word,
        en:    item.en    || '',
        ru:    item.ru    || '',
        ex_nl: item.ex_nl || '',
        ex_en: item.ex_en || '',
        ex_ru: item.ex_ru || '',
      }, lang, level, null);
    } catch(e) {
      _markRowError(placeholder, word, e);
    }
  }

  statusEl.textContent = `✅ Готово: ${done} новых слов${skipped ? `, пропущено дублей: ${skipped}` : ''}`;
  genBtn.disabled = false;
}

// Same as _callOllama but uses topic-panel Ollama settings
async function _callOllamaForTopic(lessonName, word, lang, level) {
  const langLabel = lang === 'nl' ? 'Dutch' : 'English';
  const prompt = `You are a language learning assistant. Create a vocabulary entry for a language course.
Lesson: "${lessonName}"
Input language: ${langLabel}
CEFR level: ${level || 'A2'}
Word: "${word}"

Return a JSON array with ONE object with exactly these keys:
- "nl": Dutch word with article if noun
- "en": natural English translation (1-3 words)
- "ru": natural Russian translation — proper literary Russian, NOT word-for-word
- "ex_nl": one short Dutch example sentence (${level || 'A2'} level). Surround the studied word with ** markers, e.g. "Ik moet de **rekening** betalen."
- "ex_en": that sentence in English. Surround the corresponding word with ** markers, e.g. "I need to pay the **bill**."
- "ex_ru": that sentence in Russian. Surround the corresponding word with ** markers, e.g. "Мне нужно оплатить **счёт**."
- The value of "en" must be the base/dictionary form of the word marked with ** in "ex_en"
- The value of "ru" must be the base/dictionary form of the word marked with ** in "ex_ru"

Return ONLY a JSON array. No markdown, no fences, no explanation.`;

  const body = {
    model:   _topicOllamaModel(),
    messages: [
      { role: 'system', content: 'Return ONLY valid JSON arrays, no markdown.' },
      { role: 'user',   content: prompt }
    ],
    stream: false,
    format: 'json'
  };

  const resp = await fetch(_topicOllamaUrl() + '/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(90000)
  });
  if (!resp.ok) throw new Error(`Ollama HTTP ${resp.status}`);

  const data = await resp.json();
  const raw  = (data.message?.content || data.response || '').trim();

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch(_) {
    const m = raw.match(/\[[\s\S]*\]/);
    if (m) parsed = JSON.parse(m[0]);
    else throw new Error('Не удалось разобрать ответ Ollama');
  }
  if (!Array.isArray(parsed)) {
    const keys = Object.keys(parsed);
    if (keys.length === 1 && Array.isArray(parsed[keys[0]])) parsed = parsed[keys[0]];
    else parsed = [parsed];
  }
  return parsed;
}

// ════════════════════════════════════════════════════════════════
//  TABS
// ════════════════════════════════════════════════════════════════
function switchTab(name) {
  document.querySelectorAll('.up-tab').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.up-panel').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-'   + name).classList.add('active');
  document.getElementById('panel-' + name).classList.add('active');
  if (name === 'db') {
    dbLoad();
  }
  if (name === 'share') {
    shareLessonsLoad();
  }
}

// ════════════════════════════════════════════════════════════════
//  WORD DATABASE TAB
// ════════════════════════════════════════════════════════════════

// ── State ───────────────────────────────────────────────────────
// Share lessons
let _shareLessonsLoaded = false;

async function shareLessonsLoad(force) {
  const listEl = document.getElementById('share-lessons-list');
  const statusEl = document.getElementById('share-lessons-status');
  const box = document.getElementById('share-link-box');
  if (!listEl || !statusEl) return;
  if (_shareLessonsLoaded && !force) return;

  statusEl.textContent = 'Загружаю уроки...';
  listEl.innerHTML = '';
  if (box) box.style.display = 'none';
  try {
    const resp = await apiFetch('/api/share/source_lessons');
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || 'Не удалось загрузить уроки');
    _shareLessonsLoaded = true;
    renderShareLessons(data.lessons || []);
  } catch (e) {
    statusEl.textContent = 'Ошибка: ' + e.message;
  }
}

function renderShareLessons(lessons) {
  const listEl = document.getElementById('share-lessons-list');
  const statusEl = document.getElementById('share-lessons-status');
  if (!listEl || !statusEl) return;
  listEl.innerHTML = '';

  if (!lessons.length) {
    statusEl.textContent = 'Пока нет загруженных уроков.';
    updateShareSelection();
    return;
  }

  statusEl.textContent = '';
  lessons.forEach(item => {
    const lesson = item.lesson || item.lesson_title || '';
    const count = Number(item.words_count || 0);
    const words = Array.isArray(item.words) ? item.words : [];
    const row = document.createElement('div');
    row.className = 'share-lesson-item';
    row.dataset.lesson = lesson;
    row.innerHTML = `
      <div class="share-lesson-row">
        <div class="share-lesson-main">
          <input type="checkbox" class="share-lesson-check" value="${_esc(lesson)}" aria-label="Выбрать урок ${_esc(lesson)}">
          <button type="button" class="share-lesson-name" aria-label="Показать слова урока ${_esc(lesson)}">${_esc(lesson)}</button>
        </div>
        <div class="share-lesson-meta">${count} слов</div>
      </div>
      <div class="share-lesson-words"></div>
    `;
    const wordsEl = row.querySelector('.share-lesson-words');
    wordsEl.innerHTML = words.length
      ? words.map(w => `
          <div class="share-word-line">
            <span>${_esc(w.nl || '')}</span>
            <span>${_esc(w.en || '')}</span>
            <span>${_esc(w.ru || '')}</span>
          </div>
        `).join('')
      : '<div style="color:#94a3b8">В этом уроке нет слов.</div>';
    row.querySelector('.share-lesson-name').addEventListener('click', () => {
      row.classList.toggle('is-open');
    });
    row.querySelector('.share-lesson-check').addEventListener('change', updateShareSelection);
    listEl.appendChild(row);
  });
  updateShareSelection();
}

function getSelectedShareLessons() {
  return Array.from(document.querySelectorAll('.share-lesson-check:checked'))
    .map(el => (el.value || '').trim())
    .filter(Boolean);
}

function updateShareSelection() {
  const countEl = document.getElementById('share-selected-count');
  const btn = document.getElementById('share-create-btn');
  const selected = getSelectedShareLessons();
  if (countEl) countEl.textContent = selected.length ? `Выбрано уроков: ${selected.length}` : '';
  if (btn) btn.disabled = selected.length === 0;
}

function _ruPlural(n, one, few, many) {
  const mod10 = Math.abs(n) % 10;
  const mod100 = Math.abs(n) % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}

async function createShareLink() {
  const statusEl = document.getElementById('share-lessons-status');
  const box = document.getElementById('share-link-box');
  const input = document.getElementById('share-link-input');
  const btn = document.getElementById('share-create-btn');
  const lessons = getSelectedShareLessons();
  if (!statusEl || !box || !input || !btn) return;
  if (!lessons.length) {
    statusEl.textContent = 'Выберите хотя бы один урок.';
    return;
  }

  const oldText = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Создаю...';
  statusEl.textContent = '';

  try {
    const resp = await apiFetch('/api/share/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lessons }),
    });
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || 'Не удалось создать ссылку');
    input.value = data.url;
    box.style.display = 'flex';
    input.focus();
    input.select();
    const lessonCount = Number(data.lessons_count || lessons.length);
    const wordCount = Number(data.words_count || 0);
    statusEl.textContent = `Ссылка создана: ${lessonCount} ${_ruPlural(lessonCount, 'урок', 'урока', 'уроков')}, ${wordCount} ${_ruPlural(wordCount, 'слово', 'слова', 'слов')}.`;
  } catch (e) {
    statusEl.textContent = 'Ошибка: ' + e.message;
  } finally {
    btn.textContent = oldText || 'Создать ссылку';
    updateShareSelection();
  }
}

async function copyShareLink() {
  const input = document.getElementById('share-link-input');
  const statusEl = document.getElementById('share-lessons-status');
  if (!input || !input.value) return;
  try {
    await navigator.clipboard.writeText(input.value);
    if (statusEl) statusEl.textContent = 'Ссылка скопирована.';
  } catch (_) {
    input.focus();
    input.select();
    if (statusEl) statusEl.textContent = 'Скопируйте ссылку из поля.';
  }
}

const db = {
  page:       1,
  perPage:    50,
  total:      0,
  pages:      1,
  query:      '',
  saveTimers: {},   // wordId → timer
  audio:      null, // current HTMLAudioElement
};

// ── Search debounce ─────────────────────────────────────────────
let _dbSearchTimer = null;
function dbSearchDebounced() {
  clearTimeout(_dbSearchTimer);
  _dbSearchTimer = setTimeout(() => {
    db.query = document.getElementById('db-search').value.trim();
    db.page  = 1;
    dbLoad();
  }, 350);
}

// ── Load words from server ───────────────────────────────────────
async function dbLoad() {
  const loading = document.getElementById('db-loading');
  const table   = document.getElementById('db-table');
  loading.style.display = '';
  table.style.display   = 'none';

  try {
    const qs   = new URLSearchParams({ page: db.page, per_page: db.perPage, q: db.query });
    const resp = await apiFetch('/api/words?' + qs);
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || 'Server error');

    db.total = data.total;
    db.pages = data.pages;
    document.getElementById('db-count').textContent = `${data.total} слов`;

    dbRender(data.words);
    dbRenderPager();
    loading.style.display = 'none';
    table.style.display   = '';
  } catch(e) {
    loading.style.display = '';
    loading.textContent   = '❌ ' + e.message;
  }
}

async function findDuplicateWords() {
  const panel = document.getElementById('dupes-panel');
  const statusEl = document.getElementById('dupes-status');
  const listEl = document.getElementById('dupes-list');
  if (!panel || !statusEl || !listEl) return;

  panel.style.display = 'block';
  statusEl.textContent = 'Ищу дубли...';
  listEl.innerHTML = '';

  try {
    const resp = await apiFetch('/api/words/duplicates');
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || 'Server error');
    renderDuplicateWords(data.groups || []);
    statusEl.textContent = data.groups_count
      ? `Найдено групп: ${data.groups_count}, лишних повторов: ${data.duplicates_count}.`
      : 'Дубли не найдены.';
  } catch (e) {
    statusEl.textContent = 'Ошибка: ' + e.message;
  }
}

function closeDuplicateWords() {
  const panel = document.getElementById('dupes-panel');
  if (panel) panel.style.display = 'none';
}

function renderDuplicateWords(groups) {
  const listEl = document.getElementById('dupes-list');
  if (!listEl) return;
  listEl.innerHTML = '';
  if (!groups.length) {
    listEl.innerHTML = '<div style="color:#64748b;font-size:13px">Повторяющихся NL слов нет.</div>';
    return;
  }

  groups.forEach(group => {
    const box = document.createElement('div');
    box.className = 'dupe-group';
    const items = Array.isArray(group.items) ? group.items : [];
    box.innerHTML = `
      <div class="dupe-group-head">${_esc(group.key)} · ${Number(group.count || items.length)} шт.</div>
      <div class="dupe-items">
        ${items.map(item => `
          <div class="dupe-item" data-id="${item.id}">
            <div>
              <strong>${_esc(item.nl || '')}</strong>
              <div class="dupe-lesson">${_esc(item.lesson || '')} · ${_esc(item.number || '')}</div>
            </div>
            <div>${_esc(item.en || '')}</div>
            <div>${_esc(item.ru || '')}</div>
            <div class="dupe-actions">
              <button type="button" class="ghost-btn" style="padding:4px 8px;font-size:12px" onclick="showDuplicateInDb(${_jsArg(item.nl || '')})">Показать</button>
              <button type="button" class="del-row-btn" title="Удалить дубль" onclick="openDuplicateDeleteModal(${item.id}, this)">✕</button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
    listEl.appendChild(box);
  });
}

function showDuplicateInDb(word) {
  const search = document.getElementById('db-search');
  if (!search) return;
  search.value = word || '';
  db.query = search.value.trim();
  db.page = 1;
  dbLoad();
}

function openDuplicateDeleteModal(wordId, btn) {
  const row = btn.closest('.dupe-item');
  if (!row) return;
  const cells = row.children;
  const word = cells[0]?.querySelector('strong')?.textContent?.trim() || '';
  const lesson = cells[0]?.querySelector('.dupe-lesson')?.textContent?.trim() || '';
  const en = cells[1]?.textContent?.trim() || '';
  const ru = cells[2]?.textContent?.trim() || '';

  pendingDuplicateDelete = { wordId, btn };

  const modal = document.getElementById('dupe-delete-modal');
  const wordEl = document.getElementById('dupe-delete-word');
  const lessonEl = document.getElementById('dupe-delete-lesson');
  const translationsEl = document.getElementById('dupe-delete-translations');
  const confirmBtn = document.getElementById('dupe-delete-confirm');
  if (!modal || !wordEl || !lessonEl || !translationsEl || !confirmBtn) return;

  wordEl.textContent = word || 'Без слова';
  lessonEl.textContent = lesson ? `Урок: ${lesson}` : '';
  translationsEl.textContent = [en, ru].filter(Boolean).join(' · ');
  confirmBtn.disabled = false;
  confirmBtn.textContent = 'Удалить';
  modal.classList.add('is-open');
  modal.setAttribute('aria-hidden', 'false');
  confirmBtn.focus();
}

function closeDuplicateDeleteModal() {
  const modal = document.getElementById('dupe-delete-modal');
  if (modal) {
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
  }
  pendingDuplicateDelete = null;
}

async function confirmDuplicateDelete() {
  if (!pendingDuplicateDelete) return;
  const { wordId, btn } = pendingDuplicateDelete;
  const confirmBtn = document.getElementById('dupe-delete-confirm');
  if (confirmBtn) {
    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Удаляю...';
  }
  try {
    const resp = await apiFetch(`/api/words/${wordId}`, { method: 'DELETE' });
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || 'Ошибка удаления');
    const row = btn.closest('.dupe-item');
    if (row) row.remove();
    await findDuplicateWords();
    dbLoad();
    closeDuplicateDeleteModal();
  } catch(e) {
    alert('Ошибка: ' + e.message);
    if (confirmBtn) {
      confirmBtn.disabled = false;
      confirmBtn.textContent = 'Удалить';
    }
  }
}

// ── Render table rows ────────────────────────────────────────────
function dbRender(words) {
  const tbody = document.getElementById('db-body');
  tbody.innerHTML = '';

  if (!words.length) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#94a3b8;padding:20px">Ничего не найдено</td></tr>';
    return;
  }

  words.forEach(w => {
    const tr = document.createElement('tr');
    tr.dataset.id = w.id;

    const audioHtml = _dbAudioButtons(w);
    const diffHtml  = w.difficult
      ? `<span class="diff-badge">⭐</span>`
      : `<span style="color:#d1d5db">—</span>`;

    tr.innerHTML = `
      <td class="cell-lesson editable" contenteditable="true" data-field="lesson">${_esc(w.lesson)}</td>
      <td class="cell-with-ex">
        <div class="cell-word" contenteditable="true" data-field="nl">${_esc(w.nl)}</div>
        <div class="cell-ex"   contenteditable="true" data-field="ex_nl">${_esc(w.ex_nl)}</div>
      </td>
      <td class="cell-with-ex">
        <div class="cell-word" contenteditable="true" data-field="en">${_esc(w.en)}</div>
        <div class="cell-ex"   contenteditable="true" data-field="ex_en">${_esc(w.ex_en)}</div>
      </td>
      <td class="cell-with-ex">
        <div class="cell-word" contenteditable="true" data-field="ru">${_esc(w.ru)}</div>
        <div class="cell-ex"   contenteditable="true" data-field="ex_ru">${_esc(w.ex_ru)}</div>
      </td>
      <td style="white-space:nowrap">${audioHtml}</td>
      <td class="cell-diff">${diffHtml}</td>
      <td style="white-space:nowrap">
        <button class="refresh-row-btn" title="Перегенерировать через Ollama" onclick="dbRegenWord(${w.id},this)">🔄</button>
        <button class="del-row-btn"     title="Удалить слово"                 onclick="dbDelete(${w.id},this)">✕</button>
      </td>
    `;

    tr.querySelectorAll('[data-field]').forEach(cell => {
      cell.addEventListener('blur',    () => dbScheduleSave(w.id, tr));
      cell.addEventListener('keydown', e => {
        if (e.key === 'Enter') { e.preventDefault(); cell.blur(); }
        if (e.key === 'Escape') { dbLoad(); }
      });
    });

    tbody.appendChild(tr);
  });
}

// ── Audio buttons ────────────────────────────────────────────────
function _dbAudioButtons(w) {
  const langs = [
    { key: 'audio_nl', label: 'NL' },
    { key: 'audio_en', label: 'EN' },
    { key: 'audio_ru', label: 'RU' },
  ];
  const btns = langs
    .filter(l => w[l.key])
    .map(l => {
      const path = w[l.key].startsWith('/') ? w[l.key] : '/static/' + w[l.key];
      return `<button class="audio-btn" onclick="dbPlayAudio(this,'${_esc(path)}')">▶ ${l.label}</button>`;
    })
    .join('');
  return `<div class="audio-cell">${btns}</div>`;
}

// ── Play audio ───────────────────────────────────────────────────
function dbPlayAudio(btn, src) {
  if (db.audio) { db.audio.pause(); db.audio.currentTime = 0; }
  document.querySelectorAll('.audio-btn.playing').forEach(b => b.classList.remove('playing'));

  const audio = new Audio(src);
  db.audio = audio;
  btn.classList.add('playing');
  audio.play().catch(() => {});
  audio.onended = () => btn.classList.remove('playing');
}

// ── Collect row data and schedule save ───────────────────────────
function dbScheduleSave(wordId, row) {
  clearTimeout(db.saveTimers[wordId]);
  db.saveTimers[wordId] = setTimeout(() => dbSave(wordId, row), 600);
}

async function dbSave(wordId, row) {
  const fields = {};

  row.querySelectorAll('[data-field]').forEach(cell => {
    fields[cell.dataset.field] = cell.textContent.trim();
  });

  row.classList.add('saving');
  try {
    const resp = await apiFetch(`/api/words/${wordId}`, {
      method:  'PUT',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(fields),
    });
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error);
    row.classList.remove('saving');
    row.classList.add('saved');
    setTimeout(() => row.classList.remove('saved'), 1200);
  } catch(e) {
    row.classList.remove('saving');
    row.style.outline = '2px solid #f87171';
    setTimeout(() => { row.style.outline = ''; }, 2000);
  }
}

// ── Delete word ──────────────────────────────────────────────────
async function dbDelete(wordId, btn) {
  if (!confirm('Удалить это слово из базы?')) return;
  const tr = btn.closest('tr');
  try {
    const resp = await apiFetch(`/api/words/${wordId}`, { method: 'DELETE' });
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error);
    tr.remove();
    db.total--;
    document.getElementById('db-count').textContent = `${db.total} слов`;
  } catch(e) {
    alert('Ошибка: ' + e.message);
  }
}

// ── Regenerate word via Ollama ───────────────────────────────────
async function dbRegenWord(wordId, btn) {
  const tr     = btn.closest('tr');
  const nl     = tr.querySelector('[data-field="nl"]')?.textContent?.trim()     || '';
  const lesson = tr.querySelector('[data-field="lesson"]')?.textContent?.trim() || '';
  if (!nl) return;

  const level = document.getElementById('db-regen-level')?.value || 'A2';

  const origText   = btn.textContent;
  btn.textContent  = '⏳';
  btn.disabled     = true;
  tr.style.opacity = '0.6';

  try {
    const items = await _callOllamaForTopic(lesson, nl, 'nl', level);
    const item  = Array.isArray(items) ? items[0] : items;
    if (!item) throw new Error('Ollama вернула пустой ответ');

    const setCell = (field, val) => {
      const el = tr.querySelector(`[data-field="${field}"]`);
      if (el) el.textContent = val || '';
    };
    setCell('en',    item.en);
    setCell('ru',    item.ru);
    setCell('ex_nl', item.ex_nl);
    setCell('ex_en', item.ex_en);
    setCell('ex_ru', item.ex_ru);

    await dbSave(wordId, tr);

    tr.classList.add('saved');
    setTimeout(() => tr.classList.remove('saved'), 1500);
  } catch(e) {
    tr.style.outline = '2px solid #f87171';
    setTimeout(() => { tr.style.outline = ''; }, 2000);
    console.error('dbRegenWord:', e);
    alert(`Ошибка генерации: ${e.message}`);
  } finally {
    btn.textContent  = origText;
    btn.disabled     = false;
    tr.style.opacity = '';
  }
}

// ── Pagination ───────────────────────────────────────────────────
function dbRenderPager() {
  const pager = document.getElementById('db-pager');
  if (db.pages <= 1) { pager.innerHTML = ''; return; }

  let html = `<button ${db.page <= 1 ? 'disabled' : ''} onclick="dbGoPage(${db.page-1})">‹</button>`;

  const WING = 2;
  for (let i = 1; i <= db.pages; i++) {
    if (i === 1 || i === db.pages || (i >= db.page - WING && i <= db.page + WING)) {
      html += `<button class="${i === db.page ? 'active' : ''}" onclick="dbGoPage(${i})">${i}</button>`;
    } else if (i === db.page - WING - 1 || i === db.page + WING + 1) {
      html += `<span class="pager-info">…</span>`;
    }
  }

  html += `<button ${db.page >= db.pages ? 'disabled' : ''} onclick="dbGoPage(${db.page+1})">›</button>`;
  html += `<span class="pager-info">${db.page} / ${db.pages}</span>`;
  pager.innerHTML = html;
}

function dbGoPage(p) {
  db.page = p;
  dbLoad();
}

// ════════════════════════════════════════════════════════════════
//  CSV / EXCEL FILE TAB
// ════════════════════════════════════════════════════════════════

// ── Drag & drop handlers ─────────────────────────────────────────
function fileDragOver(e) {
  e.preventDefault();
  document.getElementById('file-drop-zone').classList.add('drag-over');
}
function fileDragLeave(e) {
  document.getElementById('file-drop-zone').classList.remove('drag-over');
}
function fileDrop(e) {
  e.preventDefault();
  document.getElementById('file-drop-zone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) _fileProcess(file);
}
function fileSelected(input) {
  if (input.files[0]) _fileProcess(input.files[0]);
}

// ── Upload to server, parse, show preview ────────────────────────
async function _fileProcess(file) {
  const statusEl  = document.getElementById('file-parse-status');
  const previewEl = document.getElementById('file-preview-section');
  const dropZone  = document.getElementById('file-drop-zone');

  const name = file.name.toLowerCase();
  if (!name.endsWith('.csv') && !name.endsWith('.xlsx') && !name.endsWith('.xls')) {
    statusEl.textContent = '❌ Поддерживаются только .csv, .xlsx, .xls';
    return;
  }

  statusEl.textContent = `⏳ Разбираю «${file.name}»…`;
  previewEl.style.display = 'none';
  dropZone.querySelector('.file-drop-text').textContent = file.name;

  const form = new FormData();
  form.append('file', file);

  try {
    const resp = await apiFetch('/api/parse-file', { method: 'POST', body: form });
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error);

    statusEl.textContent = `✅ Распознано ${data.count} строк. Проверьте и нажмите «Загрузить».`;
    _fileBuildTable(data.rows);
    previewEl.style.display = '';
    previewEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch(e) {
    statusEl.textContent = `❌ Ошибка: ${e.message}`;
  }
}

// ── Build editable preview table ─────────────────────────────────
function _fileBuildTable(rows) {
  const tbody = document.getElementById('file-preview-body');
  tbody.innerHTML = '';
  rows.forEach(row => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="cell-lesson" contenteditable="true">${_esc(row.lesson)}</td>
      <td style="color:#94a3b8;font-size:11px" contenteditable="true">${_esc(row.number)}</td>
      <td class="cell-nl"    contenteditable="true">${_esc(row.nl)}</td>
      <td class="cell-en"    contenteditable="true">${_esc(row.en)}</td>
      <td class="cell-ru"    contenteditable="true">${_esc(row.ru)}</td>
      <td class="cell-ex-nl" contenteditable="true">${_esc(row.ex_nl)}</td>
      <td class="cell-ex-en" contenteditable="true">${_esc(row.ex_en)}</td>
      <td class="cell-ex-ru" contenteditable="true">${_esc(row.ex_ru)}</td>
      <td><button type="button" class="del-row-btn" onclick="this.closest('tr').remove()" title="Удалить">✕</button></td>
    `;
    tbody.appendChild(tr);
  });
}

// ── Import parsed rows to DB ─────────────────────────────────────
async function fileImportWords() {
  const uploadBtn = document.getElementById('file-upload-btn');
  const statusEl  = document.getElementById('file-upload-status');

  // Collect rows from the preview table
  const rows = [];
  document.querySelectorAll('#file-preview-body tr').forEach(tr => {
    const cells = tr.querySelectorAll('td[contenteditable]');
    if (cells.length < 8) return;
    rows.push({
      lesson:  cells[0].textContent.trim(),
      number:  cells[1].textContent.trim(),
      nl:      cells[2].textContent.trim(),
      en:      cells[3].textContent.trim(),
      ru:      cells[4].textContent.trim(),
      ex_nl:   cells[5].textContent.trim(),
      ex_en:   cells[6].textContent.trim(),
      ex_ru:   cells[7].textContent.trim(),
    });
  });

  if (!rows.length) { statusEl.textContent = 'Таблица пуста'; return; }

  // Group by lesson — reuse same API as Ollama import
  const lessonMap = new Map();
  rows.forEach(r => {
    const l = r.lesson || 'Без урока';
    if (!lessonMap.has(l)) lessonMap.set(l, []);
    lessonMap.get(l).push(r);
  });
  const lessons = Array.from(lessonMap.entries()).map(([lesson, words]) => ({ lesson, words }));

  uploadBtn.disabled = true;
  statusEl.textContent = '⏳ Загружаю в базу данных…';

  try {
    const resp = await apiFetch('/api/import-words', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ lessons }),
    });
    const data = await resp.json();
    if (data.ok) {
      statusEl.innerHTML = `✅ Загружено <strong>${data.count}</strong> слов! `
        + `<a href="/">← Посмотреть все уроки</a>`;
      document.getElementById('file-preview-section').style.display = 'none';
      document.getElementById('file-parse-status').textContent = '';
      document.getElementById('file-drop-zone').querySelector('.file-drop-text').textContent =
        'Перетащите CSV или Excel файл сюда';
      document.getElementById('file-input').value = '';
      _shareLessonsLoaded = false;
    } else {
      statusEl.textContent = `❌ ${data.error || 'Неизвестная ошибка'}`;
    }
  } catch(e) {
    statusEl.textContent = `❌ ${e.message}`;
  }
  uploadBtn.disabled = false;
}
