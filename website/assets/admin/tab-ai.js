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
    var form = h('form', {}, connection, taskCard, h('div', { class: 'adm-row' }, saveBtn, status),
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

  function load(panel) {
    return ctx.api('GET', '/api/admin/ai/settings').then(function (data) {
      settings = data.settings; tasks = data.tasks || {};
      if (!f.enabled) build(panel);
      render();
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
