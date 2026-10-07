// Standalone word database page.
const dbText = (key, params) => window.I18N.t(key, params);
const dbLegacy = text => window.I18N.legacy(text);
let pendingDuplicateDelete = null;
let wordDeleteBusy = false;

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

async function _cloudTranslateWord(word, fromLang, level, knownRu, supplied = {}) {
  const resp = await apiFetch('/api/translate/word', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ word, from_lang: fromLang, level, known_ru: knownRu || null, supplied, sense: supplied.content_sense || supplied.sense || '', context: supplied.content_context || supplied.context || '' }),
  });
  const data = await resp.json();
  if (!data.ok) throw new Error(data.error || dbText('database.cloud_error'));
  return [data];
}

const db = {
  page:       1,
  perPage:    50,
  total:      0,
  pages:      1,
  query:      '',
  saveTimers: {},   // wordId → timer
  audio:      null, // current HTMLAudioElement
  languages:  [
    {code: 'nl', native: 'Nederlands'},
    {code: 'en', native: 'English'},
    {code: 'ru', native: 'Русский'},
  ],
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
    db.languages = Array.isArray(data.languages) && data.languages.length ? data.languages : db.languages;
    document.getElementById('db-count').textContent = dbText('database.count', {count:data.total});
    document.getElementById('db-search').placeholder =
      dbText('database.search', {languages:db.languages.map(language => language.code.toUpperCase()).join(', ')});

    dbRenderHead();
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
  statusEl.textContent = dbText('database.finding_duplicates');
  listEl.innerHTML = '';

  try {
    const resp = await apiFetch('/api/words/duplicates');
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || 'Server error');
    renderDuplicateWords(data.groups || []);
    statusEl.textContent = data.groups_count
      ? dbText('database.duplicate_counts', {groups:data.groups_count, duplicates:data.duplicates_count})
      : dbText('database.no_duplicates');
  } catch (e) {
    statusEl.textContent = dbText('common.error') + ': ' + e.message;
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
    listEl.innerHTML = `<div style="color:#64748b;font-size:13px">${dbText('database.no_nl_duplicates')}</div>`;
    return;
  }

  groups.forEach(group => {
    const box = document.createElement('div');
    box.className = 'dupe-group';
    const items = Array.isArray(group.items) ? group.items : [];
    box.innerHTML = `
      <div class="dupe-group-head">${_esc(group.key)} · ${dbText('database.items', {count:Number(group.count || items.length)})}</div>
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
              <button type="button" class="ghost-btn" onclick="showDuplicateInDb(${_jsArg(item.nl || '')})">Показать</button>
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
  if (wordDeleteBusy) return;
  const duplicateRow = btn.closest('.dupe-item');
  const row = duplicateRow || btn.closest('tr');
  if (!row) return;
  const cells = row.children;
  const words = duplicateRow ? [] : Array.from(row.querySelectorAll('.cell-word')).map(cell => cell.textContent.trim());
  const word = duplicateRow ? cells[0]?.querySelector('strong')?.textContent?.trim() : words[0];
  const lesson = duplicateRow ? cells[0]?.querySelector('.dupe-lesson')?.textContent?.trim() : row.querySelector('.cell-lesson')?.textContent?.trim();
  const translations = duplicateRow ? [cells[1]?.textContent?.trim(), cells[2]?.textContent?.trim()] : words.slice(1);

  pendingDuplicateDelete = { wordId, btn, row, isDuplicate: !!duplicateRow };

  const modal = document.getElementById('dupe-delete-modal');
  const wordEl = document.getElementById('dupe-delete-word');
  const lessonEl = document.getElementById('dupe-delete-lesson');
  const translationsEl = document.getElementById('dupe-delete-translations');
  const confirmBtn = document.getElementById('dupe-delete-confirm');
  if (!modal || !wordEl || !lessonEl || !translationsEl || !confirmBtn) return;

  wordEl.textContent = word || dbText('database.unnamed');
  lessonEl.textContent = lesson ? dbLegacy('Урок') + ': ' + lesson : '';
  translationsEl.textContent = translations.filter(Boolean).join(' · ');
  document.getElementById('word-delete-error').textContent = '';
  confirmBtn.disabled = false;
  confirmBtn.textContent = dbText('common.delete');
  modal.classList.add('is-open');
  modal.setAttribute('aria-hidden', 'false');
  document.body.classList.add('modal-open');
  document.getElementById('word-delete-cancel').focus();
}

function closeDuplicateDeleteModal() {
  if (wordDeleteBusy) return;
  const modal = document.getElementById('dupe-delete-modal');
  if (modal) {
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
  }
  document.body.classList.remove('modal-open');
  pendingDuplicateDelete?.btn?.focus();
  pendingDuplicateDelete = null;
}

async function confirmDuplicateDelete() {
  if (!pendingDuplicateDelete || wordDeleteBusy) return;
  const { wordId, row, isDuplicate } = pendingDuplicateDelete;
  wordDeleteBusy = true;
  document.getElementById('word-delete-error').textContent = '';
  const confirmBtn = document.getElementById('dupe-delete-confirm');
  if (confirmBtn) {
    confirmBtn.disabled = true;
    confirmBtn.textContent = dbText('database.deleting');
  }
  try {
    const resp = await apiFetch(`/api/words/${wordId}`, { method: 'DELETE' });
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || dbText('database.delete_error'));
    if (row) row.remove();
    wordDeleteBusy = false;
    closeDuplicateDeleteModal();
    if (isDuplicate || document.getElementById('dupes-panel').style.display === 'block') await findDuplicateWords();
    await dbLoad();
  } catch(e) {
    wordDeleteBusy = false;
    document.getElementById('word-delete-error').textContent = dbText('common.error') + ': ' + e.message;
    if (confirmBtn) {
      confirmBtn.disabled = false;
      confirmBtn.textContent = dbText('common.delete');
    }
  }
}

// ── Render table rows ────────────────────────────────────────────
function dbRenderHead() {
  const row = document.getElementById('db-head-row');
  if (!row) return;
  row.innerHTML = `
    <th class="cell-lesson">Урок</th>
    ${db.languages.map(language => `
      <th title="${_esc(language.native || language.name || language.code)}">${_esc(String(language.code || '').toUpperCase())}</th>
    `).join('')}
    <th>⭐</th>
    <th></th>
  `;
}

function dbRender(words) {
  const tbody = document.getElementById('db-body');
  tbody.innerHTML = '';

  if (!words.length) {
    tbody.innerHTML = `<tr><td colspan="${db.languages.length + 3}" style="text-align:center;color:#94a3b8;padding:20px">Ничего не найдено</td></tr>`;
    return;
  }

  words.forEach(w => {
    const tr = document.createElement('tr');
    tr.dataset.id = w.id;

    const diffHtml  = w.difficult
      ? `<span class="diff-badge">⭐</span>`
      : `<span style="color:#d1d5db">—</span>`;

    tr.innerHTML = `
      <td class="cell-lesson editable" contenteditable="true" data-field="lesson">${_esc(w.lesson)}</td>
      ${db.languages.map(language => `
        <td class="cell-with-ex">
          <div class="cell-word-line">
            <div class="cell-word" contenteditable="true" data-field="${_esc(language.code)}">${_esc(w[language.code] || '')}</div>
            ${_dbAudioButton(w, language.code)}
          </div>
          <div class="cell-ex" contenteditable="true" data-field="ex_${_esc(language.code)}">${_esc(w[`ex_${language.code}`] || '')}</div>
        </td>
      `).join('')}
      <td class="cell-diff">${diffHtml}</td>
      <td style="white-space:nowrap">
        <button class="refresh-row-btn" title="Дополнить из общей базы" onclick="dbRegenWord(${w.id},this)">🔄</button>
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
function _dbAudioButton(w, languageCode) {
  const source = w[`audio_${languageCode}`];
  if (!source) return '';
  const path = source.startsWith('/') ? source : '/static/' + source;
  const src = _esc(path).replace(/"/g, '&quot;');
  const label = _esc(`${dbLegacy('Аудио')} ${languageCode.toUpperCase()}`).replace(/"/g, '&quot;');
  return `<button type="button" class="audio-btn" data-src="${src}" title="${label}" aria-label="${label}" onclick="dbPlayAudio(this,this.dataset.src)">🔊</button>`;
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
function dbDelete(wordId, btn) {
  openDuplicateDeleteModal(wordId, btn);
}

// ── Regenerate word via сервер ───────────────────────────────────
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
    const supplied = {};
    tr.querySelectorAll('[data-field]').forEach(cell => { supplied[cell.dataset.field] = cell.textContent.trim(); });
    const items = await _cloudTranslateWord(nl, 'nl', '', null, supplied);
    const item  = Array.isArray(items) ? items[0] : items;
    if (!item) throw new Error(dbText('database.empty_response'));

    const setCell = (field, val) => {
      const el = tr.querySelector(`[data-field="${field}"]`);
      if (el && !el.textContent.trim() && val) el.textContent = val;
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
    alert(dbText('database.generation_error', {message:e.message}));
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


document.addEventListener('DOMContentLoaded', dbLoad);
document.getElementById('dupe-delete-modal').addEventListener('click', (event) => {
  if (event.target.id === 'dupe-delete-modal') closeDuplicateDeleteModal();
});
document.addEventListener('keydown', (event) => {
  const modal = document.getElementById('dupe-delete-modal');
  if (!modal.classList.contains('is-open')) return;
  if (event.key === 'Escape') closeDuplicateDeleteModal();
  if (event.key === 'Tab') {
    const buttons = Array.from(modal.querySelectorAll('button:not(:disabled)'));
    const first = buttons[0], last = buttons[buttons.length - 1];
    if ((event.shiftKey && document.activeElement === first) || (!event.shiftKey && document.activeElement === last)) {
      event.preventDefault();
      (event.shiftKey ? last : first)?.focus();
    }
  }
});
document.addEventListener('hello-name-ready', dbLoad);
