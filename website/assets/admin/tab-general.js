/* Admin tab 1 — «Общее»: users, account type, family links, activity, delete. */
(function () {
  'use strict';
  var ctx, h, tbl;

  function relationRow(u, rel) {
    var btn = h('button', { type: 'button', class: 'adm-btn small danger' }, 'Открепить');
    btn.addEventListener('click', function () {
      ctx.userAction(btn, {
        title: 'Открепить ребёнка?',
        text: 'Будет удалена только выбранная связь между взрослым и ребёнком.',
        subject: rel.description || rel.counterpart_name,
        meta: 'Взрослый ID: ' + rel.parent_user_id + ' · Ребёнок ID: ' + rel.child_user_id,
        button: 'Открепить', danger: true,
        endpoint: '/api/admin/unlink_family',
        payload: { parent_user_id: rel.parent_user_id, child_user_id: rel.child_user_id },
        done: 'Связь взрослого с ребёнком удалена.'
      });
    });
    return h('div', { class: 'adm-family' },
      h('span', {}, (rel.direction === 'parent_of' ? '🧒 Ребёнок: ' : '👤 Взрослый: ') + rel.counterpart_name), btn);
  }

  function actions(u) {
    if (u.is_admin) return h('button', { type: 'button', class: 'adm-btn small', disabled: true }, 'Админ');
    var btn = h('button', { type: 'button', class: 'adm-btn small danger' }, 'Удалить');
    btn.addEventListener('click', function () {
      ctx.userAction(btn, {
        title: 'Удалить пользователя?',
        text: 'Пользователь и все его данные будут удалены. При следующем входе он зарегистрируется заново.',
        subject: u.display_name, meta: 'ID: ' + u.user_id + ' · ' + (u.username ? '@' + u.username : 'без username'),
        button: 'Удалить пользователя', danger: true,
        endpoint: '/api/admin/delete_user', payload: { user_id: u.user_id },
        done: 'Пользователь удален.'
      });
    });
    return btn;
  }

  function render(data) {
    ctx.table(tbl, ['Пользователь', 'Telegram / User ID', 'Присоединился', 'Тип аккаунта', 'Семейные связи',
      'Уроки', 'Слова', 'Последняя активность', 'Действия'],
    data.users.map(function (u) {
      var child = u.account_type === 'child';
      return h('tr', {},
        ctx.userCell(u),
        h('td', { class: 'adm-num' }, u.user_id),
        h('td', {}, u.created_at || '—'),
        h('td', {}, h('span', { class: 'adm-pill' + (child ? ' ok' : '') }, (child ? '🧒 ' : '👤 ') + u.account_type_label)),
        h('td', { class: 'adm-wrap-cell' }, (u.family_relations || []).length
          ? u.family_relations.map(function (rel) { return relationRow(u, rel); })
          : h('span', { class: 'adm-muted' }, 'Нет связей')),
        h('td', { class: 'adm-num' }, ctx.num(u.lessons_count)),
        h('td', { class: 'adm-num' }, ctx.num(u.words_count)),
        h('td', { class: 'adm-num' }, ctx.fmtDateTime(u.last_event_ts)),
        h('td', {}, actions(u)));
    }));
  }

  PLAdmin.register('general', {
    mount: function (panel, c) {
      ctx = c; h = c.h;
      tbl = h('table', { class: 'adm-table adm-table-general' });
      panel.append(ctx.card('Пользователи', ctx.wrap(tbl)));
      ctx.onOverview(render);
      ctx.overview();
    },
    show: function () { ctx.overview(true); }
  });
})();
