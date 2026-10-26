/* Admin tab 2 — «Подписки»: status, provider, trial, period, manual grant/revoke,
 * plus the session-only tariff preview (/api/admin/plan-preview). */
(function () {
  'use strict';
  var ctx, h, tbl, previewStatus, matrix, previewButtons = [];

  var MATRIX_ROWS = [
    ['price_eur', 'Цена, €/мес'], ['learning', 'Обучение'], ['manual_words', 'Ручное добавление слов'],
    ['exercises', 'Упражнения'], ['mcp', 'MCP'], ['ads', 'Реклама'], ['ai_paid', 'Платные ИИ-функции'],
    ['family', 'Семейная панель'], ['max_children', 'Детей максимум']
  ];

  function manageButton(u) {
    if (u.is_admin) return h('button', { type: 'button', class: 'adm-btn small', disabled: true }, 'Админ');
    var who = { subject: u.display_name, meta: 'ID: ' + u.user_id + ' · ' + (u.username ? '@' + u.username : 'без username') };
    var btn;
    if (u.is_unlimited) {
      btn = h('button', { type: 'button', class: 'adm-btn small danger' }, 'Отозвать');
      btn.addEventListener('click', function () {
        ctx.userAction(btn, Object.assign({
          title: 'Отозвать безлимит?',
          text: 'Ручной безлимит будет снят. Дальше доступ будет зависеть от trial или подписки.',
          button: 'Отозвать', danger: true,
          endpoint: '/api/admin/revoke_access', payload: { user_id: u.user_id }, done: 'Безлимитный доступ отозван.'
        }, who));
      });
    } else {
      btn = h('button', { type: 'button', class: 'adm-btn small primary' }, 'Безлимит');
      btn.addEventListener('click', function () {
        ctx.userAction(btn, Object.assign({
          title: 'Выдать безлимит?',
          text: 'Пользователь получит бессрочный доступ к приложению.',
          button: 'Выдать безлимит',
          endpoint: '/api/admin/grant_access', payload: { user_id: u.user_id }, done: 'Безлимитный доступ выдан.'
        }, who));
      });
    }
    return btn;
  }

  function render(data) {
    ctx.table(tbl, ['Пользователь', 'Telegram / User ID', 'Подписка', 'Provider', 'Trial до', 'Period до',
      'Отмена в конце периода', 'Доступ до', 'Управление'],
    data.users.map(function (u) {
      var cls = u.is_unlimited ? 'unlimited' : u.subscription_active ? 'ok' : 'off';
      return h('tr', {},
        ctx.userCell(u),
        h('td', { class: 'adm-num' }, u.user_id),
        h('td', {}, h('span', { class: 'adm-pill ' + cls }, u.subscription_status)),
        h('td', {}, u.subscription_provider || '—'),
        h('td', { class: 'adm-num' }, ctx.fmtDate(u.trial_ends_at)),
        h('td', { class: 'adm-num' }, ctx.fmtDate(u.current_period_ends_at)),
        h('td', {}, u.cancel_at_period_end ? 'Да' : 'Нет'),
        h('td', { class: 'adm-num' }, u.is_unlimited ? 'Безлимит' : ctx.fmtDateTime(u.access_until)),
        h('td', {}, manageButton(u)));
    }));
  }

  // ------------------------------------------------------------ plan preview
  function yes(v) { return v === true ? '✓' : v === false ? '—' : String(v); }

  function renderPreview(data) {
    var preview = data.preview || '';
    previewButtons.forEach(function (b) {
      b.classList.toggle('is-current', (b.dataset.plan === 'exit' ? '' : b.dataset.plan) === preview);
    });
    var st = data.settings || {};
    previewStatus.textContent = (preview ? 'Активен предпросмотр: ' + preview.toUpperCase() : 'Обычный режим администратора') +
      ' · Платный ИИ: ' + (st.paid_ai_enabled ? 'включён' : 'выключен глобально') +
      ' · Реклама: ' + String(st.ads_mode || 'off').toUpperCase() + ' (вкладка «Реклама»)' +
      ' · Ограничения тарифов для пользователей: ' + (st.enforce_plan_limits ? 'применяются' : 'не применяются (только в предпросмотре)');
    var codes = Object.keys(data.plans || {});
    ctx.table(matrix, [''].concat(codes.map(function (c) { return c.toUpperCase(); })),
      MATRIX_ROWS.map(function (row) {
        return h('tr', {}, h('td', {}, row[1]), codes.map(function (c) { return h('td', { class: 'adm-center' }, yes(data.plans[c][row[0]])); }));
      }));
  }

  function previewCard() {
    previewStatus = h('div', { class: 'adm-note' }, 'Загрузка…');
    matrix = h('table', { class: 'adm-table adm-table-compact' });
    var row = h('div', { class: 'adm-row' });
    [['free', 'Free'], ['premium', 'Premium'], ['family', 'Family'], ['exit', 'Выйти из предпросмотра']].forEach(function (p) {
      var b = h('button', { type: 'button', class: 'adm-btn small', 'data-plan': p[0] }, p[1]);
      b.addEventListener('click', function () {
        ctx.api('POST', '/api/admin/plan-preview', { plan: p[0] })
          .then(function (data) {
            renderPreview(data);
            ctx.flash(p[0] === 'exit' ? 'Предпросмотр выключен.' : 'Предпросмотр ' + p[1] + ' включён — откройте приложение.', 'ok');
          })
          .catch(function (e) { ctx.flash('Ошибка: ' + e.message, 'err'); });
      });
      previewButtons.push(b);
      row.append(b);
    });
    row.append(h('a', { class: 'adm-btn small', href: ctx.APP_ORIGIN + '/', target: '_blank', rel: 'noopener' }, 'Открыть приложение ↗'));
    return ctx.card('Предпросмотр тарифа',
      h('p', { class: 'adm-note' }, 'Показывает приложение так, как его видит пользователь выбранного тарифа. Действует только в этой сессии браузера: реальные права, подписка, платежи и данные не меняются, другие пользователи не затронуты.'),
      row, previewStatus, ctx.wrap(matrix));
  }

  PLAdmin.register('subscriptions', {
    mount: function (panel, c) {
      ctx = c; h = c.h;
      tbl = h('table', { class: 'adm-table adm-table-subs' });
      panel.append(previewCard(), ctx.card('Подписки пользователей', ctx.wrap(tbl)));
      ctx.onOverview(render);
      this.show();
    },
    show: function () {
      ctx.overview(true);
      ctx.api('GET', '/api/admin/plan-preview').then(renderPreview)
        .catch(function (e) { previewStatus.textContent = 'Ошибка: ' + e.message; });
    }
  });
})();
