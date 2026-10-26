/* Admin tab 3 — «Затраты и лимиты»: TTS budget/limits, AI token usage, resets. */
(function () {
  'use strict';
  var ctx, h, ttsBox, aiBox, tbl;

  function stat(label, value, meta, cls) {
    return h('div', { class: 'adm-stat' },
      h('div', { class: 'adm-stat-label' }, label),
      h('div', { class: 'adm-stat-value' + (cls ? ' ' + cls : '') }, value),
      meta ? h('div', { class: 'adm-stat-meta' }, meta) : null);
  }

  function saveLimit(btn, payload, done) {
    btn.disabled = true;
    return ctx.api('POST', '/api/admin/tts_usage/limit', payload)
      .then(function () { ctx.flash(done, 'ok'); return ctx.overview(true); })
      .catch(function (e) { ctx.flash('Ошибка: ' + e.message, 'err'); })
      .then(function () { btn.disabled = false; });
  }

  function renderTts(t) {
    var pct = Number(t.limit_percent || 0);
    var input = h('input', { type: 'number', min: '1', class: 'adm-input adm-input-limit', value: t.character_limit });
    var save = h('button', { type: 'button', class: 'adm-btn small primary' }, 'Сохранить');
    save.addEventListener('click', function () {
      var limit = Number(input.value);
      if (!Number.isInteger(limit) || limit <= 0) { ctx.flash('Введите положительный лимит символов.', 'err'); return; }
      saveLimit(save, { monthly_character_limit: limit }, 'Общий месячный лимит сохранён.');
    });
    var used = stat('Использовано символов', ctx.num(t.characters) + ' / ' + ctx.num(t.character_limit),
      'Осталось: ' + ctx.num(t.characters_remaining) + ' · ' + pct + '%');
    used.insertBefore(h('div', { class: 'adm-progress' },
      h('span', { class: pct >= 100 ? 'danger' : pct >= 80 ? 'warn' : '', style: { width: Math.min(100, pct) + '%' } })), used.lastChild);
    var limitCard = h('div', { class: 'adm-stat' },
      h('div', { class: 'adm-stat-label' }, 'Общий месячный лимит'),
      h('div', { class: 'adm-row' }, input, save),
      h('div', { class: 'adm-stat-meta' }, 'Сброс бюджета: ' + ctx.fmtDateTime(t.next_reset_at) + ' · ' + (t.timezone || '')));
    ttsBox.replaceChildren(
      used,
      stat('Фактические запросы gTTS', ctx.num(t.total_requests),
        h('span', {}, h('span', { class: 'adm-ok' }, ctx.num(t.successful_requests) + ' успешно'), ' · ',
          h('span', { class: 'adm-err' }, ctx.num(t.failed_requests) + ' ошибок'))),
      stat('Заблокировано лимитом', ctx.num(t.blocked_requests), 'Без обращения к сервису озвучивания', 'err'),
      limitCard);
  }

  function renderAi(a) {
    var reset = h('button', { type: 'button', class: 'adm-btn small danger' }, 'Сбросить AI');
    reset.addEventListener('click', function () {
      ctx.userAction(reset, {
        title: 'Сбросить все AI-токены?',
        text: 'У всех пользователей накопительные токены и счётчики AI-запросов станут равны нулю.',
        subject: 'Все пользователи', meta: 'Накопительная статистика за всё время',
        button: 'Сбросить все AI-токены', danger: true,
        endpoint: '/api/admin/translation_usage/reset', payload: {}, done: 'Все AI-токены сброшены.'
      });
    });
    var errors = stat('Ошибки AI-запросов', ctx.num(a.failed_requests), 'Накопительно', 'err');
    errors.append(reset);
    aiBox.replaceChildren(
      stat('Всего токенов', ctx.num(a.total_tokens), 'Без автоматического месячного сброса'),
      stat('Входные токены', ctx.num(a.prompt_tokens), 'Промпт и контекст'),
      stat('Выходные токены', ctx.num(a.completion_tokens), 'Ответ модели'),
      stat('Успешные AI-запросы', ctx.num(a.successful_requests), 'Переводы, предложения и тематические слова', 'ok'),
      errors);
  }

  function userRow(u) {
    var who = { subject: u.display_name, meta: 'ID: ' + u.user_id + ' · ' + (u.username ? '@' + u.username : 'без username') };
    var input = h('input', { type: 'number', min: '1', class: 'adm-input adm-input-limit', placeholder: 'Безлимит',
      value: u.tts_character_limit == null ? '' : u.tts_character_limit });
    var save = h('button', { type: 'button', class: 'adm-btn small' }, 'Сохранить');
    save.addEventListener('click', function () {
      var raw = input.value.trim();
      var limit = raw === '' ? null : Number(raw);
      if (limit !== null && (!Number.isInteger(limit) || limit <= 0)) {
        ctx.flash('Лимит пользователя должен быть положительным числом или пустым для безлимита.', 'err');
        return;
      }
      saveLimit(save, { user_id: u.user_id, monthly_character_limit: limit },
        limit === null ? 'Пользовательский лимит отключён.' : 'Пользовательский лимит сохранён.');
    });
    var resetTts = h('button', { type: 'button', class: 'adm-btn small' }, 'Сбросить TTS-статистику');
    resetTts.addEventListener('click', function () {
      ctx.userAction(resetTts, Object.assign({
        title: 'Сбросить счётчик Google TTS?',
        text: 'У выбранного пользователя успешные и неуспешные запросы станут равны нулю. Израсходованный месячный бюджет символов не изменится.',
        button: 'Сбросить счётчик', danger: true,
        endpoint: '/api/admin/tts_usage/reset', payload: { user_id: u.user_id }, done: 'Счётчик Google TTS пользователя сброшен.'
      }, who));
    });
    var resetAi = h('button', { type: 'button', class: 'adm-btn small' }, 'Сбросить AI');
    resetAi.addEventListener('click', function () {
      ctx.userAction(resetAi, Object.assign({
        title: 'Сбросить AI-токены?',
        text: 'У выбранного пользователя накопительные токены и счётчики AI-запросов станут равны нулю.',
        button: 'Сбросить AI-токены', danger: true,
        endpoint: '/api/admin/translation_usage/reset', payload: { user_id: u.user_id }, done: 'AI-токены пользователя сброшены.'
      }, who));
    });
    return h('tr', {},
      ctx.userCell(u),
      h('td', { class: 'adm-num' }, u.user_id),
      h('td', { class: 'adm-num' }, ctx.num(u.tts_total_requests) + ' (' + ctx.num(u.tts_successful_requests) + '/' + ctx.num(u.tts_failed_requests) + ')'),
      h('td', { class: 'adm-num' }, ctx.num(u.tts_characters)),
      h('td', { class: 'adm-num adm-err' }, ctx.num(u.tts_blocked_requests)),
      h('td', {}, h('div', { class: 'adm-row nowrap' }, input, save)),
      h('td', { class: 'adm-num' }, ctx.num(u.translation_total_tokens)),
      h('td', { class: 'adm-num' }, ctx.num(u.translation_prompt_tokens)),
      h('td', { class: 'adm-num' }, ctx.num(u.translation_completion_tokens)),
      h('td', { class: 'adm-num adm-ok' }, ctx.num(u.translation_successful_requests)),
      h('td', { class: 'adm-num adm-err' }, ctx.num(u.translation_failed_requests)),
      h('td', {}, h('div', { class: 'adm-row nowrap' }, resetTts, resetAi)));
  }

  function render(data) {
    renderTts(data.tts_usage || {});
    renderAi(data.translation_usage || {});
    ctx.table(tbl, ['Пользователь', 'Telegram / User ID', 'TTS запросы', 'TTS символы', 'Заблокировано', 'Лимит пользователя',
      'AI-токены', 'Вход', 'Выход', 'AI успешно', 'AI ошибки', 'Действия'], data.users.map(userRow));
  }

  PLAdmin.register('costs', {
    mount: function (panel, c) {
      ctx = c; h = c.h;
      ttsBox = h('div', { class: 'adm-stats' });
      aiBox = h('div', { class: 'adm-stats adm-stats-5' });
      tbl = h('table', { class: 'adm-table adm-table-costs' });
      panel.append(
        h('h2', { class: 'adm-section-title' }, 'Озвучивание · текущий месяц'), ttsBox,
        h('h2', { class: 'adm-section-title' }, 'AI-токены · перевод и генерация · за всё время'), aiBox,
        ctx.card('По пользователям', ctx.wrap(tbl)),
        h('p', { class: 'adm-note' }, 'Сброс TTS-статистики не восстанавливает израсходованный месячный бюджет символов.'));
      ctx.onOverview(render);
      ctx.overview();
    },
    show: function () { ctx.overview(true); }
  });
})();
