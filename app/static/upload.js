// upload.js — страница загрузки слов с генерацией через сервер

let lessonCounter = 0;
let uploadLessons = [];

async function loadUploadLessons() {
  try {
    const response = await apiFetch('/api/user_lessons');
    const lessons = await response.json();
    if (!response.ok || !Array.isArray(lessons)) throw new Error('Не удалось загрузить уроки');
    uploadLessons = lessons;
    document.querySelectorAll('.lesson-existing').forEach(fillLessonChoices);
  } catch (error) {
    document.getElementById('gen-status').textContent = '⚠ Список уроков недоступен. Можно указать название вручную.';
  }
}

function fillLessonChoices(select) {
  const selected = select.value;
  select.replaceChildren(new Option('Новый урок — укажите название', ''));
  uploadLessons.forEach(item => select.add(new Option(`${item.lesson} (${item.words_count} слов)`, item.lesson)));
  select.value = selected;
}

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
      <label>Добавить в урок:
        <select class="lesson-existing" aria-label="Выбрать существующий урок"></select>
      </label>
      <p class="lesson-hint">Название урока обязательно. Введите одно слово или список: каждое слово с новой строки.</p>
      <textarea class="words-ta" placeholder="Формат 1 — одно NL слово в строке:&#10;het huis&#10;de kamer&#10;&#10;Формат 2 — пары NL + RU (с пустой строкой между):&#10;bewegen&#10;двигаться&#10;&#10;Start&#9;de kamer&#9;&#10;комната"></textarea>
      <p class="lesson-hint">Формат определяется автоматически: если есть русский текст — NL+RU, иначе — только NL слова</p>
    </div>
    <div class="lesson-gen-status" id="lgs-${idx}"></div>
    <div class="regen-row" id="regen-row-${idx}" style="display:none;margin-top:6px">
      <button type="button" class="ghost-btn regen-lesson-btn"
        onclick="regenerateLesson(${idx})">🔄 Перегенерировать урок</button>
      <span class="regen-hint" style="font-size:11px;color:#94a3b8;margin-left:8px">
        Перегенерирует все слова с текущим уровнем и исправлениями
      </span>
    </div>
  `;
  container.appendChild(div);
  const choice = div.querySelector('.lesson-existing');
  fillLessonChoices(choice);
  choice.addEventListener('change', () => {
    const name = div.querySelector('.lesson-name');
    name.value = choice.value;
    name.readOnly = Boolean(choice.value);
    if (!choice.value) name.focus();
  });
  div.querySelector('.lesson-name').required = true;
  div.querySelector('.lesson-name').maxLength = 200;
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

// ── AI source toggle (сервер локально / Облако через AI Platform) ────









async function _cloudTranslateWord(word, fromLang, level, knownRu, supplied = {}) {
  const resp = await apiFetch('/api/translate/word', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ word, from_lang: fromLang, level, known_ru: knownRu || null, supplied, sense: supplied.content_sense || supplied.sense || '', context: supplied.content_context || supplied.context || '' }),
  });
  const data = await resp.json();
  if (!data.ok) throw new Error(data.error || 'Ошибка облака');
  return [data];
}

async function _cloudSuggestTopicWords(topic, lang, level, count, existingWords) {
  const resp = await apiFetch('/api/generate/topic', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, lang, level, count, existing_words: existingWords }),
  });
  const data = await resp.json();
  if (!data.ok) throw new Error(data.error || 'Ошибка облака');
  return data.words || [];
}

async function _cloudTranslateLanguage(sourceWord, sourceSentence, sourceLangName, targetLangName, supplied = {}) {
  const resp = await apiFetch('/api/translate/language', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_word: sourceWord, source_sentence: sourceSentence,
      source_lang_name: sourceLangName, target_lang_name: targetLangName, supplied, sense: supplied.content_sense || supplied.sense || '', context: supplied.content_context || supplied.context || '',
    }),
  });
  const data = await resp.json();
  if (!data.ok) throw new Error(data.error || 'Ошибка облака');
  if (data.missing_fields?.length) throw new Error('Недостающий контент: ' + data.missing_fields.join(', ') + '. Внешний сервис ещё не подключён.');
  return { word: data.word || '', sentence: data.sentence || '' };
}

// ── сервер helpers ──────────────────────────────────────────────






function _cefrLevel() {
  return (document.getElementById('cefr-level')?.value || 'A2');
}



async function _resolveWords(lessonName, words, lang, level) {
  return _cloudTranslateWord(words[0], lang, level);
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

  for (const block of blocks) {
    if (block.querySelector('.words-ta').value.trim() && !block.querySelector('.lesson-name').value.trim()) {
      statusEl.textContent = '⚠ Укажите название урока или выберите существующий урок.';
      block.querySelector('.lesson-name').focus();
      return;
    }
  }

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
    const words = rawWords;
    const dupes = [];
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
    const deferred = [];
    const MAX_RETRIES = 3;

    for (const wordObj of words) {
      const wordLabel = wordObj.nl;
      totalDone++;
      doneInBlock++;
      if (lgs) lgs.textContent = `⏳ ${doneInBlock}/${words.length}: ${wordLabel}`;

      const placeholder = _addPendingRow(lessonName, wordLabel);

      let succeeded = false;
      let lastError;

      for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
        statusEl.textContent = attempt > 1
          ? `🔄 ${totalDone}/${totalWords}: «${wordLabel}» — попытка ${attempt}/${MAX_RETRIES}`
          : `⏳ ${totalDone}/${totalWords}: «${wordLabel}» (${lessonName})`;

        try {
          let item;
          if (fmt === 'nl+ru') {
            const items = await _resolveKnownTranslation(lessonName, wordObj.nl, wordObj.ru || '', level);
            item = Array.isArray(items) ? items[0] : items;
          } else {
            const items = await _resolveWords(lessonName, [wordLabel], lang, level);
            item = Array.isArray(items) ? items[0] : items;
          }
          if (!item) throw new Error('Сервер вернул пустой ответ');
          _fillRow(placeholder, {
            lesson: lessonName, word: wordLabel,
            nl:    item.nl    || wordObj.nl  || '',
            en:    item.en    || '',
            ru:    item.ru    || wordObj.ru  || '',
            ex_nl: item.ex_nl || '', ex_en: item.ex_en || '', ex_ru: item.ex_ru || '',
          }, lang, level, wordObj.ru || null);
          succeeded = true;
          break;
        } catch(e) {
          lastError = e;
        }
      }

      if (!succeeded) {
        placeholder.style.opacity = '';
        placeholder.style.background = '#fef9c3';
        placeholder.innerHTML = `
          <td class="cell-lesson" contenteditable="true">${_esc(lessonName)}</td>
          <td colspan="6" style="color:#92400e;font-size:12px">⏳ «${_esc(wordLabel)}» — не удалось после ${MAX_RETRIES} попыток, повторим в конце…</td>
          <td></td>
        `;
        deferred.push({ wordObj, placeholder });
      }
    }

    // Retry deferred words at the end of the block
    for (const { wordObj, placeholder } of deferred) {
      const wordLabel = wordObj.nl;
      statusEl.textContent = `🔄 Повтор: «${wordLabel}» (${lessonName})`;
      try {
        let item;
        if (fmt === 'nl+ru') {
          const items = await _resolveKnownTranslation(lessonName, wordObj.nl, wordObj.ru || '', level);
          item = Array.isArray(items) ? items[0] : items;
        } else {
          const items = await _resolveWords(lessonName, [wordLabel], lang, level);
          item = Array.isArray(items) ? items[0] : items;
        }
        if (!item) throw new Error('Сервер вернул пустой ответ');
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
      msg = `Сервер вернул данные в неверном формате для «${word}» — нажмите 🔄 для повтора`;
    } else if (raw.includes('Failed to fetch') || raw.includes('NetworkError')) {
      msg = 'Сервер недоступен — проверьте подключение';
    } else if (raw.includes('timeout') || raw.includes('AbortError')) {
      msg = `Время ожидания истекло для «${word}» — нажмите 🔄`;
    } else if (raw.includes('JSON') || raw.includes('разобрать')) {
      msg = `Не удалось разобрать ответ сервера для «${word}» — нажмите 🔄`;
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
      const items = await _resolveKnownTranslation(lesson, word, knownRu, level);
      item = Array.isArray(items) ? items[0] : items;
    } else {
      const items = await _resolveWords(lesson, [word], lang, level);
      item = Array.isArray(items) ? items[0] : items;
    }
    if (!item) throw new Error('Сервер вернул пустой ответ');
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
      const items = await _resolveWords(lessonName, [word], lang, level);
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
      level: tr.dataset.level || '',
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
    const l = row.lesson.trim();
    if (!l) throw new Error('Укажите название урока для каждой строки.');
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
  if (rows.some(row => !row.lesson)) { statusEl.textContent = '⚠ Укажите название урока для каждой строки.'; return; }

  uploadBtn.disabled = true;
  statusEl.textContent = '⏳ Загружаю в базу данных...';

  try {
    const lessons = _groupByLesson(rows);
    const resp = await apiFetch('/api/import-words', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lessons, idempotency_key: crypto.randomUUID() })
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
      await loadUploadLessons();
    } else {
      statusEl.textContent = `❌ Ошибка: ${data.error || 'неизвестная ошибка'}`;
    }
  } catch(e) {
    statusEl.textContent = `❌ Ошибка: ${e.message}`;
  }

  uploadBtn.disabled = false;
}

// ════════════════════════════════════════════════════════════════
//  PASTE TAB  (NL + RU format from сервер / Telegram)
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


async function _resolveKnownTranslation(lessonName, nl, ru, level) {
  return _cloudTranslateWord(nl, 'nl', level, ru);
}

addLesson();
loadUploadLessons();
initAdminSubscriptionsLink();


// ════════════════════════════════════════════════════════════════
//  TOPIC GENERATOR TAB
// ════════════════════════════════════════════════════════════════












async function _suggestWordsByTopic(topic, lang, level, count, existingWords) {
  return _cloudSuggestTopicWords(topic, lang, level, count, existingWords);
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
  const existingWords = [];

  // Step 2: ask сервер for word suggestions
  statusEl.textContent = `⏳ Запрашиваю ${count} слов по теме «${topic}» у сервер…`;
  let suggested;
  try {
    suggested = await _suggestWordsByTopic(topic, lang, level, count, existingWords);
  } catch(e) {
    statusEl.textContent = `❌ Ошибка сервер: ${e.message}`;
    genBtn.disabled = false;
    return;
  }

  // Step 3: filter duplicates
  const newWords = suggested;

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
      const items = await _resolveTopicWord(lessonName, word, lang, level);
      const item  = Array.isArray(items) ? items[0] : items;
      if (!item) throw new Error('Сервер вернул пустой ответ');
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

// Same as _resolveWords but uses topic-panel сервер settings
async function _resolveTopicWord(lessonName, word, lang, level) {
  return _cloudTranslateWord(word, lang, level);
}

// ════════════════════════════════════════════════════════════════
//  TABS
// ════════════════════════════════════════════════════════════════
function switchTab(name) {
  document.querySelectorAll('.up-tab').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.up-panel').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-'   + name).classList.add('active');
  document.getElementById('panel-' + name).classList.add('active');
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
let _shareLessons = [];
let _shareLanguageOptions = [];
let _sharePreferredLanguages = [];
let _shareEditingLesson = null;
let _shareMissingTasks = [];
let _shareGenerationRunning = false;

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
    _shareLessons = data.lessons || [];
    _shareLanguageOptions = data.language_options || [];
    _sharePreferredLanguages = data.preferred_languages || [];
    renderShareLessons(_shareLessons);
    renderShareChildren(data.children || []);
  } catch (e) {
    statusEl.textContent = 'Ошибка: ' + e.message;
  }
}

function startShareLessonRename(button, lesson) {
  if (!button || button.dataset.editing === '1') return;
  const statusEl = document.getElementById('share-lessons-status');
  const original = String(lesson || '').trim();
  button.dataset.editing = '1';
  button.contentEditable = 'true';
  button.classList.add('is-editing');
  button.focus();
  try {
    const range = document.createRange();
    range.selectNodeContents(button);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  } catch (_) {}

  let finished = false;
  const stopEditing = () => {
    button.contentEditable = 'false';
    button.classList.remove('is-editing');
    delete button.dataset.editing;
    button.removeEventListener('keydown', onKeydown);
    button.removeEventListener('blur', cancel);
  };
  const cancel = () => {
    if (finished) return;
    finished = true;
    button.textContent = original;
    stopEditing();
  };
  const commit = async () => {
    if (finished) return;
    const nextLesson = String(button.textContent || '').replace(/\s+/g, ' ').trim();
    if (!nextLesson) {
      if (statusEl) statusEl.textContent = 'Название урока не может быть пустым.';
      cancel();
      return;
    }
    if (nextLesson === original) {
      cancel();
      return;
    }
    finished = true;
    stopEditing();
    button.textContent = nextLesson;
    if (statusEl) statusEl.textContent = 'Сохраняю название урока...';
    try {
      const response = await apiFetch('/api/user_lessons/rename', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({lesson: original, new_lesson: nextLesson})
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        const message = data.error === 'lesson_exists'
          ? 'Урок с таким названием уже существует.'
          : 'Не удалось изменить название урока.';
        throw new Error(message);
      }
      _shareLessonsLoaded = false;
      await shareLessonsLoad(true);
      const refreshedStatus = document.getElementById('share-lessons-status');
      if (refreshedStatus) refreshedStatus.textContent = 'Название урока сохранено.';
    } catch (error) {
      button.textContent = original;
      if (statusEl) statusEl.textContent = error.message || 'Не удалось изменить название урока.';
    }
  };
  function onKeydown(event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      event.stopPropagation();
      commit();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      event.stopPropagation();
      cancel();
    }
  }
  button.addEventListener('keydown', onKeydown);
  button.addEventListener('blur', cancel);
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
    const editableName = item.editable_name === true;
    const words = Array.isArray(item.words) ? item.words : [];
    const languages = Array.isArray(item.languages) ? item.languages : [];
    const languageText = languages.map(lang => lang.native || lang.name || String(lang.code || '').toUpperCase()).join(', ');
    const missingLanguages = _sharePreferredLanguages.filter(lang =>
      words.some(word =>
        !String(word[lang.code] || '').trim() || !String(word[`ex_${lang.code}`] || '').trim()
      )
    );
    const languageButtons = missingLanguages.map(lang => `
      <button type="button" class="share-add-language-btn" data-language="${_esc(lang.code)}">
        + Добавить: ${_esc(lang.native || lang.name || String(lang.code || '').toUpperCase())}
      </button>
    `).join('');
    const row = document.createElement('div');
    row.className = 'share-lesson-item';
    row.dataset.lesson = lesson;
    row.innerHTML = `
      <div class="share-lesson-row">
        <div class="share-lesson-main">
          <input type="checkbox" class="share-lesson-check" value="${_esc(lesson)}" aria-label="Выбрать урок ${_esc(lesson)}">
          <button type="button" class="share-lesson-name" aria-label="${editableName ? 'Изменить название урока' : 'Название урока'} ${_esc(lesson)}">${_esc(lesson)}</button>
          ${languageText ? `<span class="share-lesson-languages">· ${_esc(languageText)}</span>` : ''}
        </div>
        <div class="share-lesson-side">
          <div class="share-lesson-language-actions">${languageButtons}</div>
          <div class="share-lesson-meta">${count} слов</div>
          <button type="button" class="share-lesson-preview-btn" aria-label="Показать слова урока ${_esc(lesson)}">▾</button>
        </div>
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
    row.querySelector('.share-lesson-name').addEventListener('click', event => {
      event.stopPropagation();
      if (editableName) startShareLessonRename(event.currentTarget, lesson);
      else row.classList.toggle('is-open');
    });
    row.querySelector('.share-lesson-preview-btn').addEventListener('click', () => {
      row.classList.toggle('is-open');
    });
    row.querySelector('.share-lesson-check').addEventListener('change', updateShareSelection);
    row.querySelectorAll('.share-add-language-btn').forEach(button => {
      button.addEventListener('click', () => addShareLessonLanguage(lesson, button.dataset.language));
    });
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
  const childBtn = document.getElementById('share-child-btn');
  if (childBtn) childBtn.disabled = selected.length === 0;
  hideShareLanguageWarning();
}

function renderShareChildren(children) {
  const actions = document.getElementById('share-child-actions');
  const select = document.getElementById('share-child-select');
  const status = document.getElementById('share-child-status');
  if (!actions || !select || !status) return;
  select.innerHTML = '';
  if (!children.length) {
    actions.style.display = 'none';
    status.textContent = 'Чтобы добавлять уроки ребёнку, сначала привяжите его аккаунт.';
    return;
  }
  children.forEach(child => {
    const option = document.createElement('option');
    option.value = child.user_id;
    const languageText = (child.languages || []).map(language => language.native || language.name || language.code).join(', ');
    option.textContent = `${child.display_name || child.username || child.user_id}${languageText ? ` — ${languageText}` : ''}`;
    select.appendChild(option);
  });
  select._children = children;
  select.addEventListener('change', hideShareLanguageWarning);
  actions.style.display = 'flex';
  status.textContent = '';
  updateShareSelection();
}

function openShareLanguageEditor(lessonName) {
  _shareEditingLesson = _shareLessons.find(item => item.lesson === lessonName) || null;
  if (!_shareEditingLesson) return;
  const editor = document.getElementById('share-language-editor');
  document.getElementById('share-language-title').textContent = `Языки урока: ${lessonName}`;
  renderShareLanguageTable();
  document.getElementById('share-language-status').textContent = '';
  editor.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeShareLanguageEditor() {
  if (_shareGenerationRunning) return;
  document.getElementById('share-language-editor')?.classList.remove('open');
  document.body.style.overflow = '';
  _shareEditingLesson = null;
}

function renderShareLanguageTable() {
  if (!_shareEditingLesson) return;
  const languages = _shareEditingLesson.languages || [];
  const head = document.getElementById('share-language-head');
  const body = document.getElementById('share-language-body');
  head.innerHTML = `<tr><th>№</th>${languages.map(language =>
    `<th>${_esc(language.native || language.name || language.code)}</th>`
  ).join('')}</tr>`;
  body.innerHTML = (_shareEditingLesson.words || []).map(word => `
    <tr data-word-id="${Number(word.id)}">
      <td>${_esc(word.number || '')}</td>
      ${languages.map(language => `
        <td class="share-language-cell">
          <div class="share-language-word" contenteditable="true" data-field="${_esc(language.code)}">${_esc(word[language.code] || '')}</div>
          <div class="share-language-sentence" contenteditable="true" data-field="ex_${_esc(language.code)}">${_esc(word[`ex_${language.code}`] || '')}</div>
        </td>
      `).join('')}
    </tr>
  `).join('');
  body.querySelectorAll('[data-field]').forEach(cell => {
    cell.addEventListener('keydown', async event => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        await saveShareLanguageCell(cell);
        cell.blur();
      }
    });
  });
}

async function saveShareLanguageCell(cell) {
  const row = cell.closest('tr');
  const wordId = Number(row?.dataset.wordId || 0);
  if (!wordId || !cell.dataset.field) return false;
  row.classList.add('saving');
  try {
    const value = cell.textContent.trim();
    const response = await apiFetch(`/api/words/${wordId}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({[cell.dataset.field]: value}),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || 'save_failed');
    const word = (_shareEditingLesson?.words || []).find(item => Number(item.id) === wordId);
    if (word) word[cell.dataset.field] = value;
    row.classList.remove('saving');
    row.classList.add('saved');
    setTimeout(() => row.classList.remove('saved'), 1000);
    return true;
  } catch (error) {
    row.classList.remove('saving');
    row.style.outline = '2px solid #f87171';
    setTimeout(() => { row.style.outline = ''; }, 1800);
    document.getElementById('share-language-status').textContent = `Ошибка сохранения: ${error.message}`;
    return false;
  }
}

async function _generateShareLanguageValue(word, targetLanguage, level) {
  const sourceLanguage = (_shareEditingLesson.languages || [])[0];
  if (!sourceLanguage) throw new Error('В уроке нет исходного языка');
  return _cloudTranslateLanguage(
    String(word[sourceLanguage.code] || '').trim(),
    String(word[`ex_${sourceLanguage.code}`] || '').trim(),
    sourceLanguage.code, targetLanguage.code,
    {[targetLanguage.code]: word[targetLanguage.code] || '', [`ex_${targetLanguage.code}`]: word[`ex_${targetLanguage.code}`] || '', content_sense: word.content_sense || '', content_context: word.content_context || ''});
}

function hideShareLanguageWarning() {
  document.getElementById('share-language-warning')?.classList.remove('open');
  _shareMissingTasks = [];
}

function getShareMissingLanguageTasks() {
  const childSelect = document.getElementById('share-child-select');
  const child = (childSelect?._children || []).find(item => String(item.user_id) === String(childSelect.value));
  if (!child) return [];
  const selected = new Set(getSelectedShareLessons());
  const tasks = [];
  _shareLessons.filter(lesson => selected.has(lesson.lesson)).forEach(lesson => {
    (child.languages || []).forEach(childLanguage => {
      const target = _shareLanguageOptions.find(option => option.code === childLanguage.code) || childLanguage;
      const missingWords = (lesson.words || []).filter(word =>
        !String(word[target.code] || '').trim() || !String(word[`ex_${target.code}`] || '').trim()
      );
      if (missingWords.length) tasks.push({lesson, target, words: lesson.words || []});
    });
  });
  return tasks;
}

function showShareLanguageWarning(tasks) {
  const grouped = new Map();
  tasks.forEach(task => {
    if (!grouped.has(task.lesson.lesson)) grouped.set(task.lesson.lesson, []);
    grouped.get(task.lesson.lesson).push(task.target.native || task.target.name || task.target.code.toUpperCase());
  });
  document.getElementById('share-language-warning-text').textContent =
    'Перед передачей нужно дополнить языки: ' + Array.from(grouped.entries())
      .map(([lesson, languages]) => `${lesson} — ${Array.from(new Set(languages)).join(', ')}`)
      .join('; ') + '.';
  document.getElementById('share-language-warning').classList.add('open');
}



async function saveGeneratedShareTranslation(word, target, generated) {
  let lastError = null;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      const response = await apiFetch(`/api/words/${word.id}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          [target.code]: generated.word,
          [`ex_${target.code}`]: generated.sentence,
        }),
      });
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.error || 'save_failed');
      word[target.code] = generated.word;
      word[`ex_${target.code}`] = generated.sentence;
      return;
    } catch (error) {
      lastError = error;
      if (attempt < 3) await new Promise(resolve => setTimeout(resolve, attempt * 500));
    }
  }
  throw new Error(`не удалось сохранить перевод: ${lastError?.message || 'save_failed'}`);
}

async function addShareLessonLanguage(lessonName, languageCode) {
  if (_shareGenerationRunning) return;
  const lesson = _shareLessons.find(item => item.lesson === lessonName);
  const target = _shareLanguageOptions.find(option => option.code === languageCode)
    || _sharePreferredLanguages.find(option => option.code === languageCode);
  if (!lesson || !target) return;
  const missingWords = (lesson.words || []).filter(word =>
    !String(word[target.code] || '').trim() || !String(word[`ex_${target.code}`] || '').trim()
  );
  if (!missingWords.length) {
    await shareLessonsLoad(true);
    return;
  }
  await runShareLanguageGeneration([{lesson, target, words: missingWords}], false);
}

async function startMissingLanguageGeneration() {
  const tasks = getShareMissingLanguageTasks();
  _shareMissingTasks = tasks;
  if (!_shareMissingTasks.length) {
    hideShareLanguageWarning();
    await assignLessonsToChild(true);
    return;
  }
  await runShareLanguageGeneration(tasks, true);
}

async function runShareLanguageGeneration(tasks, assignAfterGeneration) {
  _shareMissingTasks = tasks;
  const addBtn = document.getElementById('share-add-missing-btn');
  const status = document.getElementById('share-language-status');
  const level = document.getElementById('share-language-level').value || 'A2';
  const closeBtn = document.getElementById('share-language-close-btn');
  if (addBtn) addBtn.disabled = true;
  closeBtn.disabled = true;
  _shareGenerationRunning = true;
  let completedWords = 0;
  const totalWords = _shareMissingTasks.reduce((sum, task) => sum + task.words.length, 0);
  try {
    for (let taskIndex = 0; taskIndex < _shareMissingTasks.length; taskIndex += 1) {
      const task = _shareMissingTasks[taskIndex];
      _shareEditingLesson = task.lesson;
      if (!task.lesson.languages.some(language => language.code === task.target.code)) {
        task.lesson.languages.push(task.target);
      }
      document.getElementById('share-language-editor').classList.add('open');
      document.body.style.overflow = 'hidden';
      document.getElementById('share-language-title').textContent = `Урок ${taskIndex + 1} из ${_shareMissingTasks.length}: ${task.lesson.lesson}`;
      document.getElementById('share-language-current').textContent = `Добавляется язык: ${task.target.native || task.target.name || task.target.code}`;
      renderShareLanguageTable();
      for (const word of task.words) {
        status.textContent = `Слово ${completedWords + 1} из ${totalWords}. Урок «${task.lesson.lesson}», язык ${task.target.native || task.target.name}.`;
        const generated = await _generateShareLanguageValue(word, task.target, level);
        status.textContent = `Перевод получен. Сохраняю слово ${completedWords + 1} из ${totalWords}...`;
        await saveGeneratedShareTranslation(word, task.target, generated);
        completedWords += 1;
        renderShareLanguageTable();
      }
    }
    status.textContent = assignAfterGeneration
      ? `Все языки добавлены. Сохранено слов: ${completedWords}. Передаю уроки ребёнку...`
      : `Язык добавлен. Сохранено слов: ${completedWords}.`;
    hideShareLanguageWarning();
    _shareGenerationRunning = false;
    closeShareLanguageEditor();
    if (assignAfterGeneration) {
      await assignLessonsToChild(true);
    } else {
      await shareLessonsLoad(true);
    }
  } catch (error) {
    status.textContent = `Генерация остановлена после ${completedWords} из ${totalWords}: ${error.message}`;
  } finally {
    _shareGenerationRunning = false;
    if (addBtn) addBtn.disabled = false;
    closeBtn.disabled = false;
  }
}

async function assignLessonsToChild(skipLanguageCheck) {
  const select = document.getElementById('share-child-select');
  const status = document.getElementById('share-child-status');
  const btn = document.getElementById('share-child-btn');
  const lessons = getSelectedShareLessons();
  if (!select || !status || !btn || !lessons.length) return;
  if (!skipLanguageCheck) {
    _shareMissingTasks = getShareMissingLanguageTasks();
    if (_shareMissingTasks.length) {
      showShareLanguageWarning(_shareMissingTasks);
      status.textContent = 'В выбранных уроках не хватает языков ребёнка.';
      return;
    }
  }
  const oldText = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Добавляю...';
  status.textContent = '';
  try {
    const resp = await apiFetch('/api/share/assign_child', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ child_user_id: select.value, lessons }),
    });
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || 'Не удалось добавить уроки ребёнку');
    const childName = select.options[select.selectedIndex]?.textContent || 'ребёнку';
    status.textContent = `Добавлено для ${childName}: ${data.lessons_count} ${_ruPlural(data.lessons_count, 'урок', 'урока', 'уроков')}, ${data.count} ${_ruPlural(data.count, 'слово', 'слова', 'слов')}.`;
  } catch (e) {
    status.textContent = 'Ошибка: ' + e.message;
  } finally {
    btn.textContent = oldText;
    updateShareSelection();
  }
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
      body: JSON.stringify({ lessons, idempotency_key: crypto.randomUUID() }),
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

  if (rows.some(row => !row.lesson)) { statusEl.textContent = '⚠ Укажите название урока для каждой строки.'; return; }

  // Group by lesson — reuse same API as сервер import
  const lessonMap = new Map();
  rows.forEach(r => {
    const l = r.lesson;
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
      await loadUploadLessons();
    } else {
      statusEl.textContent = `❌ ${data.error || 'Неизвестная ошибка'}`;
    }
  } catch(e) {
    statusEl.textContent = `❌ ${e.message}`;
  }
  uploadBtn.disabled = false;
}
