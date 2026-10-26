/* ParallelLingvo admin shell (vanilla JS, no dependencies).
 *
 * The page itself holds no data and no rights. Everything comes from the
 * app backend (app.parallellingvo.app /api/admin/*) with the normal session
 * cookie; the backend checks admin rights on every call, answers CORS only
 * for this site's exact origin and requires the per-session CSRF token
 * (from /api/admin/session) for every change. Nothing is kept in
 * localStorage except the theme.
 */
(function () {
  'use strict';

  // Local development only: a page served from localhost may point at a
  // local app backend; on the real site the origin is fixed.
  var LOCAL = /^(localhost|127\.0\.0\.1)$/.test(window.location.hostname);
  var APP_ORIGIN = (LOCAL && window.PL_ADMIN_APP_ORIGIN) || 'https://app.parallellingvo.app';
  var TABS = ['general', 'subscriptions', 'costs', 'ai', 'ads'];
  var DEFAULT_TAB = 'general';

  var csrfToken = '';
  var tabs = {};
  var mounted = {};
  var overviewPromise = null;
  var overviewListeners = [];
  var lastOverview = null;
  var currentTab = '';

  function $(id) { return document.getElementById(id); }

  // ---------------------------------------------------------------- DOM utils
  function h(tag, attrs) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      var v = attrs[k];
      if (k === 'on') Object.keys(v).forEach(function (ev) { node.addEventListener(ev, v[ev]); });
      else if (k === 'class') node.className = v;
      else if (k === 'style' && typeof v === 'object') Object.assign(node.style, v);
      else if (v === true) node.setAttribute(k, '');
      else if (v !== false && v != null) node.setAttribute(k, v);
    });
    for (var i = 2; i < arguments.length; i++) append(node, arguments[i]);
    return node;
  }
  function append(node, child) {
    if (Array.isArray(child)) { child.forEach(function (c) { append(node, c); }); return; }
    if (child == null || child === false) return;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  function table(el, headers, rows, cls) {
    var tbl = el.tagName === 'TABLE' ? el : h('table', { class: 'adm-table ' + (cls || '') });
    tbl.replaceChildren(
      h('thead', {}, h('tr', {}, headers.map(function (x) { return h('th', {}, x); }))),
      h('tbody', {}, rows.length ? rows : [h('tr', {}, h('td', { colspan: headers.length, class: 'adm-empty' }, '—'))])
    );
    return tbl;
  }
  function wrap(tbl) { return h('div', { class: 'adm-table-wrap' }, tbl); }
  function card(title) {
    var c = h('div', { class: 'adm-card' });
    if (title) c.append(h('h2', { class: 'adm-card-title' }, title));
    for (var i = 1; i < arguments.length; i++) append(c, arguments[i]);
    return c;
  }
  function list(v) { return (v || []).join(', '); }
  function fmtDateTime(ms) {
    ms = Number(ms || 0);
    if (!ms) return '—';
    return new Date(ms).toLocaleString('ru-RU', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  }
  function fmtDate(ms) {
    ms = Number(ms || 0);
    return ms ? new Date(ms).toLocaleDateString('ru-RU') : '—';
  }
  function num(v) { return Number(v || 0).toLocaleString('ru-RU'); }

  // -------------------------------------------------------------------- flash
  var flashTimer = null;
  function flash(text, kind) {
    var el = $('adm-flash');
    el.textContent = text || '';
    el.className = 'adm-flash' + (kind ? ' ' + kind : '');
    clearTimeout(flashTimer);
    if (kind === 'ok') flashTimer = setTimeout(function () { el.textContent = ''; el.className = 'adm-flash'; }, 6000);
  }

  // ---------------------------------------------------------------------- API
  function api(method, path, body) {
    var opts = { method: method, credentials: 'include', headers: {} };
    if (method !== 'GET') {
      opts.headers['Content-Type'] = 'application/json';
      opts.headers['X-CSRF-Token'] = csrfToken;
      opts.body = JSON.stringify(body || {});
    }
    return fetch(APP_ORIGIN + path, opts).then(function (resp) {
      return resp.json().catch(function () { return { ok: false, error: 'bad_response' }; }).then(function (data) {
        if (resp.status === 401) showGate('signin');
        if (!resp.ok || !data.ok) {
          var msg = String(data.error || ('HTTP ' + resp.status));
          if (data.http_status) msg += ' (HTTP ' + data.http_status + ')';
          if (data.detail) msg += ': ' + data.detail;
          var err = new Error(msg);
          err.status = resp.status;
          err.data = data;
          throw err;
        }
        return data;
      });
    });
  }

  // Shared data of the General / Subscriptions / Costs tabs.
  function overview(force) {
    if (!overviewPromise || force) {
      overviewPromise = api('GET', '/api/admin/overview');
      overviewPromise.then(function (data) {
        lastOverview = data;
        overviewListeners.forEach(function (fn) { try { fn(data); } catch (e) { console.error(e); } });
      }, function (e) { flash('Ошибка загрузки пользователей: ' + e.message, 'err'); });
    }
    return overviewPromise;
  }
  // Subscribers get the current data at once (if loaded) and every refresh.
  function onOverview(fn) {
    overviewListeners.push(fn);
    if (lastOverview) fn(lastOverview);
  }

  // ------------------------------------------------------------ confirm modal
  var pendingConfirm = null;
  function confirmAction(opts) {
    return new Promise(function (resolve) {
      pendingConfirm = resolve;
      $('adm-confirm-title').textContent = opts.title || 'Подтвердите действие';
      $('adm-confirm-text').textContent = opts.text || '';
      $('adm-confirm-subject').textContent = opts.subject || '';
      $('adm-confirm-meta').textContent = opts.meta || '';
      var ok = $('adm-confirm-ok');
      ok.textContent = opts.button || 'Подтвердить';
      ok.className = 'adm-btn ' + (opts.danger ? 'danger' : 'primary');
      var modal = $('adm-confirm');
      modal.classList.add('is-open');
      modal.setAttribute('aria-hidden', 'false');
      ok.focus();
    });
  }
  function closeConfirm(result) {
    var modal = $('adm-confirm');
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    if (pendingConfirm) { var r = pendingConfirm; pendingConfirm = null; r(result); }
  }

  // --------------------------------------------------------------------- tabs
  function register(name, tab) { tabs[name] = tab; }

  function currentTabFromUrl() {
    var tab = new URLSearchParams(window.location.search).get('tab') || '';
    return TABS.indexOf(tab) >= 0 ? tab : DEFAULT_TAB;
  }

  function activate(name, push) {
    if (TABS.indexOf(name) < 0) name = DEFAULT_TAB;
    currentTab = name;
    document.querySelectorAll('.adm-tab').forEach(function (b) {
      var on = b.dataset.tab === name;
      b.classList.toggle('is-active', on);
      b.setAttribute('aria-selected', on ? 'true' : 'false');
      if (on && b.scrollIntoView) b.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    });
    document.querySelectorAll('.adm-panel').forEach(function (p) { p.hidden = p.dataset.panel !== name; });
    if (push) {
      var url = new URL(window.location.href);
      url.searchParams.set('tab', name);
      history.pushState({ tab: name }, '', url.pathname + url.search);
    }
    var panel = document.querySelector('.adm-panel[data-panel="' + name + '"]');
    var tab = tabs[name];
    if (!tab) return;
    if (!mounted[name]) {
      mounted[name] = true;
      tab.mount(panel, api_ctx);
    } else if (tab.show) {
      tab.show();
    }
  }

  // ---------------------------------------------------------------- gate/auth
  function showGate(kind, detail) {
    var gate = $('adm-gate');
    gate.hidden = false;
    $('adm-tabs').hidden = true;
    document.querySelectorAll('.adm-panel').forEach(function (p) { p.hidden = true; });
    if (kind === 'signin') {
      gate.replaceChildren(
        h('h2', { class: 'adm-card-title' }, 'Нужен вход'),
        h('p', {}, 'Войдите на главной странице через Google или Telegram под учётной записью администратора, затем вернитесь сюда.'),
        h('a', { class: 'btn btn-purple', href: '/' }, 'На главную')
      );
    } else if (kind === 'forbidden') {
      gate.replaceChildren(
        h('h2', { class: 'adm-card-title' }, 'Доступ запрещён'),
        h('p', {}, 'Этот раздел доступен только администраторам ParallelLingvo.'),
        h('a', { class: 'btn btn-outline', href: '/' }, 'На главную')
      );
    } else {
      gate.replaceChildren(
        h('h2', { class: 'adm-card-title' }, 'Сервер недоступен'),
        h('p', {}, 'Не удалось проверить доступ' + (detail ? ': ' + detail : '') + '.'),
        h('button', { type: 'button', class: 'btn btn-outline', on: { click: function () { window.location.reload(); } } }, 'Повторить')
      );
    }
  }

  function start() {
    $('adm-confirm-cancel').addEventListener('click', function () { closeConfirm(false); });
    $('adm-confirm-ok').addEventListener('click', function () { closeConfirm(true); });
    $('adm-confirm').addEventListener('click', function (e) { if (e.target === $('adm-confirm')) closeConfirm(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && pendingConfirm) closeConfirm(false); });

    fetch(APP_ORIGIN + '/api/admin/session', { credentials: 'include' })
      .then(function (resp) {
        if (resp.status === 401) { showGate('signin'); return null; }
        if (resp.status === 403) { showGate('forbidden'); return null; }
        return resp.json().then(function (data) {
          if (!resp.ok || !data.ok || data.is_admin !== true || !data.csrf_token) { showGate('forbidden'); return null; }
          return data;
        });
      })
      .then(function (data) {
        if (!data) return;
        csrfToken = data.csrf_token;
        var user = data.user || {};
        var name = [user.first_name, user.last_name].filter(Boolean).join(' ');
        var badge = $('adm-user');
        badge.textContent = (name || 'Администратор') + ' · ' + user.id;
        badge.hidden = false;
        $('adm-gate').hidden = true;
        $('adm-tabs').hidden = false;
        document.querySelectorAll('.adm-tab').forEach(function (b) {
          b.addEventListener('click', function () { activate(b.dataset.tab, true); });
        });
        window.addEventListener('popstate', function () {
          var tab = currentTabFromUrl();
          if (tab !== currentTab) activate(tab, false);  // in-tab #anchors keep the tab as is
        });
        activate(currentTabFromUrl(), false);
      })
      .catch(function (e) { showGate('error', e && e.message); });
  }

  // --------------------------------------------- shared bits of the user tabs
  function userCell(u) {
    return h('td', {},
      h('span', { class: 'adm-user-name' }, u.display_name || 'Без имени'),
      h('span', { class: 'adm-user-sub' }, u.username ? '@' + u.username : 'без username'));
  }

  // Confirm → POST → reload the shared overview, as on the old /admin/users.
  function userAction(btn, opts) {
    return confirmAction(opts).then(function (yes) {
      if (!yes) return;
      btn.disabled = true;
      return api('POST', opts.endpoint, opts.payload || {})
        .then(function () { flash(opts.done || 'Готово.', 'ok'); return overview(true); })
        .catch(function (e) { flash('Ошибка: ' + e.message, 'err'); btn.disabled = false; });
    });
  }

  var api_ctx = {
    APP_ORIGIN: APP_ORIGIN,
    api: api,
    overview: overview,
    onOverview: onOverview,
    confirm: confirmAction,
    userAction: userAction,
    userCell: userCell,
    flash: flash,
    h: h, table: table, wrap: wrap, card: card, list: list,
    fmtDate: fmtDate, fmtDateTime: fmtDateTime, num: num
  };

  window.PLAdmin = { register: register, start: start, ctx: api_ctx };
})();
