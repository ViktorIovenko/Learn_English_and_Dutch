/* Admin tab 4 — «ИИ»: connection (endpoint, model, timeout, encrypted key) and
 * per-task model/instructions. Backend: /api/admin/ai/settings (GET/POST).
 * The API key is never returned — only settings.key_configured. */
(function () {
  'use strict';
  var ctx, h, settings = null, tasks = {}, f = {}, taskNodes = {}, runtime, keyState, status, saveBtn;

  function field(label, input, hint) {
    return h('label', { class: 'adm-field' }, h('span', {}, label), input, hint ? h('span', { class: 'adm-note' }, hint) : null);
  }

  function render() {
    f.enabled.checked = !!settings.enabled;
    f.endpoint.value = settings.endpoint || '';
    f.model.value = settings.model || '';
    f.timeout.value = settings.timeout;
    f.key.value = '';
    f.clearKey.checked = false;
    keyState.textContent = settings.key_configured
      ? 'Ключ сохранён на сервере (key_configured: true).'
      : 'Ключ не задан (key_configured: false). Это допустимо только для сервиса без авторизации.';
    keyState.className = 'adm-pill ' + (settings.key_configured ? 'ok' : 'off');
    runtime.textContent = !settings.paid_ai_allowed
      ? 'Платный ИИ выключен на сервере. Настройки можно сохранить; внешние обращения заблокированы до включения PAID_AI_ENABLED.'
      : settings.active ? 'Подключение включено. Применяются действующие ограничения доступа и тарифов.'
      : settings.managed ? 'Подключение выключено. Доступен сохранённый контент.'
      : 'Подключение ещё не настроено. Пока действуют прежние серверные настройки.';
    Object.keys(taskNodes).forEach(function (code) {
      var t = (settings.tasks || {})[code] || { model: '', prompt: '' };
      taskNodes[code].model.value = t.model || '';
      taskNodes[code].prompt.value = t.prompt || '';
    });
  }

  function build(panel) {
    runtime = h('p', { class: 'adm-note adm-state' });
    keyState = h('span', { class: 'adm-pill' });
    f.enabled = h('input', { type: 'checkbox' });
    f.endpoint = h('input', { type: 'url', class: 'adm-input', maxlength: '1000', placeholder: 'https://ваш-сервис/v1/chat/completions' });
    f.model = h('input', { type: 'text', class: 'adm-input', maxlength: '200', placeholder: 'Идентификатор модели у вашего сервиса' });
    f.timeout = h('input', { type: 'number', class: 'adm-input', min: '5', max: '120', step: '1', required: true });
    f.key = h('input', { type: 'password', class: 'adm-input', maxlength: '4000', autocomplete: 'new-password',
      placeholder: 'Оставьте пустым, чтобы сохранить текущий ключ' });
    f.clearKey = h('input', { type: 'checkbox' });

    var connection = ctx.card('Подключение',
      h('p', { class: 'adm-note' }, 'Поддерживается API Chat Completions в формате OpenAI. Android, сайт и Telegram используют общие серверные функции: модель и инструкции меняются здесь без обновления клиентов. Новые настройки применяются при следующем обращении к ИИ.'),
      runtime,
      h('label', { class: 'adm-check' }, f.enabled, ' Использовать это подключение (Enabled)'),
      field('Полный HTTPS адрес API', f.endpoint),
      h('div', { class: 'adm-grid-2' }, field('Модель по умолчанию', f.model), field('Ожидание ответа, секунд', f.timeout)),
      field('Новый API-ключ', f.key, 'Ключ хранится на сервере в зашифрованном виде и не возвращается на страницу или в приложения. Ввод ключа и сохранение не отправляют запросов к ИИ.'),
      h('div', { class: 'adm-row' }, keyState, h('label', { class: 'adm-check' }, f.clearKey, ' Удалить сохранённый ключ')));

    var taskCard = ctx.card('Отдельные AI-задачи',
      h('p', { class: 'adm-note' }, 'Пустая модель задачи означает общую модель. Инструкции дополняют требования к переводу и формату ответа.'));
    Object.keys(tasks).forEach(function (code) {
      var model = h('input', { type: 'text', class: 'adm-input', maxlength: '200', placeholder: 'Использовать общую модель' });
      var prompt = h('textarea', { class: 'adm-input adm-textarea', maxlength: '8000' });
      taskNodes[code] = { model: model, prompt: prompt };
      taskCard.append(h('details', { class: 'adm-details' },
        h('summary', {}, tasks[code] + ' ', h('code', {}, code)),
        field('Модель для этой задачи (override)', model),
        field('Дополнительные инструкции', prompt)));
    });

    status = h('span', { class: 'adm-note', role: 'status' });
    saveBtn = h('button', { type: 'submit', class: 'adm-btn primary' }, 'Сохранить');
    var testOut = h('span', { class: 'adm-note', role: 'status' });
    var testBtn = h('button', { type: 'button', class: 'adm-btn' }, 'Проверить подключение');
    testBtn.addEventListener('click', function () {
      testBtn.disabled = true; testOut.className = 'adm-note'; testOut.textContent = 'Запрос к ИИ…';
      ctx.api('POST', '/api/admin/ai/test', {}).then(function (r) {
        testOut.className = 'adm-note adm-ok';
        testOut.textContent = 'Работает: «house» → «' + r.answer + '» · ' + r.model + ' · ' + r.latency_ms + ' мс · ' +
          ctx.num((r.usage || {}).total_tokens) + ' токенов';
      }).catch(function (e) {
        testOut.className = 'adm-note adm-err'; testOut.textContent = 'Ошибка: ' + e.message;
      }).then(function () { testBtn.disabled = false; loadStats(); });
    });
    connection.append(h('div', { class: 'adm-row' }, testBtn, testOut),
      h('p', { class: 'adm-note' }, 'Проверка отправляет один короткий запрос (перевод слова) через сохранённые настройки и попадает в статистику как «Проверка из админки». Сначала сохраните изменения.'));
    var form = h('form', {}, buildStats(), connection, taskCard, h('div', { class: 'adm-row' }, saveBtn, status),
      h('p', { class: 'adm-note' }, 'Выключение подключения останавливает внешние вызовы. Серверный выключатель платного ИИ и ограничения тарифов продолжают действовать.'));
    form.addEventListener('submit', save);
    panel.replaceChildren(form);
  }

  function save(ev) {
    ev.preventDefault();
    var taskData = {};
    Object.keys(taskNodes).forEach(function (code) {
      taskData[code] = { model: taskNodes[code].model.value.trim(), prompt: taskNodes[code].prompt.value };
    });
    status.className = 'adm-note'; status.textContent = 'Сохранение…'; saveBtn.disabled = true;
    ctx.api('POST', '/api/admin/ai/settings', {
      revision: settings.revision, enabled: f.enabled.checked,
      endpoint: f.endpoint.value.trim(), model: f.model.value.trim(), timeout: Number(f.timeout.value),
      api_key: f.key.value, clear_key: f.clearKey.checked, tasks: taskData
    }).then(function (data) {
      settings = data.settings; render();
      status.className = 'adm-note adm-ok'; status.textContent = 'Сохранено. Новые обращения используют эти настройки.';
    }).catch(function (e) {
      status.className = 'adm-note adm-err'; status.textContent = e.message || 'Ошибка соединения';
    }).then(function () { saveBtn.disabled = false; });
  }

  // ------------------------------------------------------------- statistics
  var CHANNELS = { web: 'Сайт (web/PWA)', telegram: 'Telegram Mini App', android: 'Android', mcp: 'MCP (ChatGPT/Claude)',
    bot: 'Telegram-бот / сервер', admin: 'Проверка из админки' };
  var STATUSES = { ok: ['успешно', 'ok'], error: ['ошибка', 'off'], invalid: ['неподходящий ответ', 'warn'],
    blocked: ['отклонён', 'warn'] };
  var BLOCK_REASONS = { disabled: 'ИИ выключен', plan: 'тариф без платного ИИ' };
  var GROUP_HEAD = ['Запросы', 'Успешно', 'Ошибки', 'Отклонено', 'Токены', 'Среднее время'];
  var st = {};

  function buildStats() {
    st.days = h('select', { class: 'adm-input' }, [1, 7, 30, 90, 365].map(function (d) {
      return h('option', { value: d, selected: d === 30 }, d === 1 ? 'Сутки' : d + ' дней');
    }));
    st.days.addEventListener('change', loadStats);
    st.kpi = h('div', { class: 'adm-stats adm-stats-6' });
    ['channel', 'operation', 'model', 'day', 'user', 'recent'].forEach(function (k) { st[k] = h('table', { class: 'adm-table' }); });
    var refresh = h('button', { type: 'button', class: 'adm-btn small' }, 'Обновить');
    refresh.addEventListener('click', loadStats);
    return ctx.card('Статистика запросов к ИИ',
      h('p', { class: 'adm-note' }, 'Все обращения к ИИ из сайта, Telegram Mini App, Android, MCP и бота проходят через это подключение и записываются здесь. Ответы из сохранённой базы переводов к ИИ не обращаются и не считаются. Тексты запросов и ответов не сохраняются.'),
      h('div', { class: 'adm-row' }, h('span', {}, 'Период:'), st.days, refresh),
      st.kpi,
      h('div', { class: 'adm-grid-2' },
        h('div', {}, h('h3', { class: 'adm-subtitle' }, 'По приложениям'), ctx.wrap(st.channel)),
        h('div', {}, h('h3', { class: 'adm-subtitle' }, 'По задачам'), ctx.wrap(st.operation))),
      h('div', { class: 'adm-grid-2' },
        h('div', {}, h('h3', { class: 'adm-subtitle' }, 'По моделям'), ctx.wrap(st.model)),
        h('div', {}, h('h3', { class: 'adm-subtitle' }, 'По дням'), ctx.wrap(st.day))),
      h('h3', { class: 'adm-subtitle' }, 'Пользователи'), ctx.wrap(st.user),
      h('h3', { class: 'adm-subtitle' }, 'Последние 100 запросов'), ctx.wrap(st.recent));
  }

  function statCard(label, value, cls) {
    return h('div', { class: 'adm-stat' }, h('div', { class: 'adm-stat-label' }, label),
      h('div', { class: 'adm-stat-value' + (cls ? ' ' + cls : '') }, value));
  }
  function metricCells(r) {
    return [h('td', { class: 'adm-num' }, ctx.num(r.requests)),
      h('td', { class: 'adm-num adm-ok' }, ctx.num(r.ok)),
      h('td', { class: 'adm-num adm-err' }, ctx.num((r.errors || 0) + (r.invalid || 0))),
      h('td', { class: 'adm-num' }, ctx.num(r.blocked)),
      h('td', { class: 'adm-num' }, ctx.num(r.total_tokens)),
      h('td', { class: 'adm-num' }, r.avg_latency_ms == null ? '—' : ctx.num(r.avg_latency_ms) + ' мс')];
  }
  function groupTable(el, title, rows, label) {
    ctx.table(el, [title].concat(GROUP_HEAD), rows.map(function (r) { return h('tr', {}, h('td', {}, label(r)), metricCells(r)); }));
  }

  function loadStats() {
    if (!st.days) return;
    ctx.api('GET', '/api/admin/ai/stats?days=' + st.days.value).then(function (r) {
      var s = r.summary;
      st.kpi.replaceChildren(
        statCard('Запросов к ИИ', ctx.num(s.requests)),
        statCard('Успешно', ctx.num(s.ok), 'ok'),
        statCard('Ошибки', ctx.num((s.errors || 0) + (s.invalid || 0)), 'err'),
        statCard('Отклонено (ИИ выключен / тариф)', ctx.num(s.blocked)),
        statCard('Токены: вход / выход', ctx.num(s.prompt_tokens) + ' / ' + ctx.num(s.completion_tokens)),
        statCard('Среднее время ответа', s.avg_latency_ms == null ? '—' : ctx.num(s.avg_latency_ms) + ' мс'));
      groupTable(st.channel, 'Приложение', r.by_channel, function (x) { return CHANNELS[x.key] || x.key; });
      groupTable(st.operation, 'Задача', r.by_operation, function (x) { return tasks[x.key] || x.key; });
      groupTable(st.model, 'Модель', r.by_model, function (x) { return x.key || '— (запрос не отправлялся)'; });
      groupTable(st.day, 'День', r.by_day.slice().reverse(), function (x) { return x.key; });
      ctx.table(st.user, ['Пользователь', 'ID'].concat(GROUP_HEAD), r.by_user.map(function (x) {
        return h('tr', {}, h('td', {}, x.name || '—'), h('td', { class: 'adm-num' }, x.key), metricCells(x));
      }));
      ctx.table(st.recent, ['Время', 'Приложение', 'Задача', 'Пользователь', 'Модель', 'Статус', 'Время ответа', 'Токены', 'Причина'],
        r.recent.map(function (x) {
          var label = STATUSES[x.status] || [x.status, ''];
          return h('tr', {}, h('td', { class: 'nowrap' }, ctx.fmtDateTime(x.at)), h('td', {}, CHANNELS[x.channel] || x.channel),
            h('td', {}, tasks[x.operation] || x.operation), h('td', { class: 'adm-num' }, x.user_id || '—'), h('td', {}, x.model || '—'),
            h('td', {}, h('span', { class: 'adm-pill ' + label[1] }, label[0])),
            h('td', { class: 'adm-num' }, x.status === 'blocked' ? '—' : ctx.num(x.latency_ms) + ' мс'),
            h('td', { class: 'adm-num' }, ctx.num(x.total_tokens)),
            h('td', { class: 'adm-wrap-cell' }, x.status === 'blocked' ? (BLOCK_REASONS[x.error] || x.error) : (x.error || '')));
        }));
    }).catch(function (e) { ctx.flash('Статистика ИИ: ' + e.message, 'err'); });
  }

  function load(panel) {
    return ctx.api('GET', '/api/admin/ai/settings').then(function (data) {
      settings = data.settings; tasks = data.tasks || {};
      if (!f.enabled) build(panel);
      render();
      loadStats();
    }).catch(function (e) { ctx.flash('ИИ: ' + e.message, 'err'); });
  }

  var panelRef;
  PLAdmin.register('ai', {
    mount: function (panel, c) { ctx = c; h = c.h; panelRef = panel; panel.append(h('div', { class: 'adm-note' }, 'Загрузка…')); load(panel); },
    // Re-read on every visit so a concurrent change is not overwritten blindly
    // (the server also rejects a stale revision).
    show: function () { if (!f.key || !f.key.value) load(panelRef); }
  });
})();
