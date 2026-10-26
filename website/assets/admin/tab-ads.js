/* Admin tab 5 — «Реклама»: the existing advertising module (app/advertising)
 * — mode OFF/PREVIEW/LIVE, Awin, advertisers, creatives, placements,
 * preview and anonymous stats. All rules (LIVE guards, creative validation,
 * membership) are enforced by the backend; this tab only calls its API. */
(function () {
  'use strict';
  var ctx, h, state = null, sim = { device: 'phone' }, el = {};
  var WIDTHS = { phone: 390, tablet: 820, desktop: 1280 };
  var MODE_INFO = {
    off: 'OFF — пользователям ничего не загружается.',
    preview: 'PREVIEW — демонстрационные баннеры только администратору в симуляции Free, без внешних запросов и трекинга.',
    live: 'LIVE — одобренные материалы Awin только пользователям Free (не детям, не trial, не платным) после согласия.'
  };

  function api(method, path, body) { return ctx.api(method, path, body); }
  function ok(text) { ctx.flash(text, 'ok'); }
  function fail(prefix) { return function (e) { ctx.flash(prefix + e.message, 'err'); }; }
  function badge(text, cls) { return h('span', { class: 'adm-pill ' + (cls || '') }, text); }
  function btn(text, cls, onClick) {
    var b = h('button', { type: 'button', class: 'adm-btn small ' + (cls || '') }, text);
    if (onClick) b.addEventListener('click', onClick);
    return b;
  }
  function input(attrs) { return h('input', Object.assign({ class: 'adm-input' }, attrs || {})); }
  function labeled(label, node, wide) { return h('label', { class: 'adm-field' + (wide ? ' wide' : '') }, h('span', {}, label), node); }
  function section(id, title) {
    var c = ctx.card(title);
    c.id = 'ads-' + id;
    for (var i = 2; i < arguments.length; i++) c.append(arguments[i]);
    return c;
  }

  // ================================================================= render
  function render(data) {
    state = data;
    renderSettings(data); renderAwin(data); renderPlacements(data);
    renderAdvertisers(data); renderCreatives(data); renderLog(data);
    renderSimButtons(data);
    if (!el.repRegion.options.length) {
      data.constants.report_regions.forEach(function (r) { el.repRegion.append(h('option', { value: r }, r)); });
    }
  }

  // ---------------------------------------------------------- settings/mode
  function renderSettings(data) {
    var s = data.settings;
    el.modeButtons.forEach(function (b) { b.classList.toggle('is-current', b.dataset.mode === s.mode); });
    el.modeInfo.textContent = MODE_INFO[s.mode] || '';
    el.env.replaceChildren(
      badge('Режим: ' + String(s.mode).toUpperCase(), s.mode === 'live' ? 'ok' : s.mode === 'preview' ? 'warn' : ''),
      badge('ADS_LIVE_ALLOWED: ' + (data.live_allowed ? '1' : '0'), data.live_allowed ? 'ok' : 'off'),
      badge('Awin API: ' + (data.awin.configured ? 'настроен' : 'не настроен'), data.awin.configured ? 'ok' : 'warn'));
    el.max.value = s.max_per_page;
    el.topics.value = ctx.list(s.preferred_topics);
    el.demo.checked = !!s.demo_creatives;
    el.demoAlways.checked = !!s.admin_demo_always;
    el.lapsed.checked = !!s.lapsed_paid_as_free;
    el.platforms.forEach(function (c) { c.checked = (s.live_platforms || []).indexOf(c.dataset.platform) >= 0; });
  }

  function buildSettings() {
    el.modeButtons = ['off', 'preview', 'live'].map(function (mode) {
      var b = btn(mode.toUpperCase(), '', function () { setMode(mode); });
      b.dataset.mode = mode;
      return b;
    });
    el.liveConfirm = input({ placeholder: 'Введите LIVE для подтверждения', size: 28, hidden: true });
    el.modeInfo = h('p', { class: 'adm-note' });
    el.env = h('div', { class: 'adm-row' });
    el.max = input({ type: 'number', min: '0', max: '4' });
    el.topics = input({ type: 'text', placeholder: 'language, education, books' });
    el.demo = h('input', { type: 'checkbox' });
    el.demoAlways = h('input', { type: 'checkbox' });
    el.lapsed = h('input', { type: 'checkbox' });
    el.platforms = [['web', 'Web (сайт и PWA)'], ['telegram', 'Telegram Mini App'], ['android', 'Android']].map(function (p) {
      var c = h('input', { type: 'checkbox' });
      c.dataset.platform = p[0];
      c._label = p[1];
      return c;
    });
    var save = h('button', { type: 'button', class: 'adm-btn primary' }, 'Сохранить настройки');
    save.addEventListener('click', function () {
      api('POST', '/api/admin/ads/settings', {
        max_per_page: Number(el.max.value), preferred_topics: el.topics.value,
        demo_creatives: el.demo.checked, admin_demo_always: el.demoAlways.checked, lapsed_paid_as_free: el.lapsed.checked,
        live_platforms: el.platforms.filter(function (c) { return c.checked; }).map(function (c) { return c.dataset.platform; })
      }).then(function (r) { render(r); ok('Настройки сохранены'); refreshPreview(); }).catch(fail('Ошибка: '));
    });
    return section('settings', 'Общие настройки',
      h('div', { class: 'adm-row' }, el.modeButtons, el.liveConfirm), el.modeInfo, el.env,
      h('p', { class: 'adm-note' }, 'LIVE включается только сервером при ADS_LIVE_ALLOWED=1, настроенном Awin API и вводе слова LIVE; показываются только материалы рекламодателей со статусом joined. В симуляции Free администратор всегда видит рекламные места (макеты), пользователи при этом ничего не видят.'),
      h('div', { class: 'adm-form' },
        labeled('Максимум баннеров на экран', el.max),
        labeled('Предпочтительные темы', el.topics),
        h('div', { class: 'adm-field' }, h('span', {}, 'Платформы LIVE'),
          el.platforms.map(function (c) { return h('label', { class: 'adm-check' }, c, ' ' + c._label); })),
        h('div', { class: 'adm-field' }, h('span', {}, 'Прочее'),
          h('label', { class: 'adm-check' }, el.demo, ' Демо-баннеры в PREVIEW'),
          h('label', { class: 'adm-check' }, el.demoAlways, ' Админу всегда показывать макеты (без симуляции Free)'),
          h('label', { class: 'adm-check' }, el.lapsed, ' Истёкшая платная подписка = Free'))),
      h('div', { class: 'adm-row' }, save));
  }

  function setMode(mode) {
    var body = { mode: mode };
    if (mode === 'live') {
      if (el.liveConfirm.hidden || el.liveConfirm.value !== 'LIVE') {
        el.liveConfirm.hidden = false;
        el.liveConfirm.focus();
        ctx.flash('Для LIVE введите слово LIVE в поле рядом и нажмите LIVE ещё раз. Сервер дополнительно проверит ADS_LIVE_ALLOWED и Awin.', 'err');
        return;
      }
      body.confirm = 'LIVE';
    }
    api('POST', '/api/admin/ads/settings', body)
      .then(function (r) { el.liveConfirm.value = ''; el.liveConfirm.hidden = true; render(r); ok('Режим: ' + mode.toUpperCase()); refreshPreview(); })
      .catch(fail('Режим не изменён: '));
  }

  // --------------------------------------------------------------------- Awin
  function renderAwin(data) {
    var last = (data.api_log || [])[0];
    el.awinState.replaceChildren(
      badge(data.awin.configured ? 'Awin configured' : 'Awin not configured', data.awin.configured ? 'ok' : 'warn'),
      badge('Publisher ID ' + (data.awin.publisher_id || '—')),
      last ? badge('Последний запрос: ' + last.operation + ' · ' + (last.ok ? 'ok' : 'ошибка') + ' · ' + ctx.fmtDateTime(last.at), last.ok ? 'ok' : 'off')
        : badge('Запросов к Awin ещё не было'));
    el.awinHint.textContent = data.awin.configured ? '' : 'Задайте AWIN_API_TOKEN на сервере, чтобы синхронизировать программы. Токен не передаётся на эту страницу.';
  }

  // ------------------------------------------------------------- placements
  function renderPlacements(data) {
    var C = data.constants;
    ctx.table(el.placements, ['Ключ', 'Страница', 'Название', 'Вкл.', 'Приоритет'].concat(C.devices.map(function (d) { return 'Размеры · ' + d; }), ['']),
      data.placements.map(function (p) {
        var enabled = h('input', { type: 'checkbox', checked: p.enabled });
        var label = input({ type: 'text', value: p.label });
        var priority = input({ type: 'number', value: p.priority, style: { width: '70px' } });
        var tr = h('tr', {}, h('td', {}, h('code', {}, p.key)), h('td', {}, p.page), h('td', {}, label), h('td', {}, enabled), h('td', {}, priority),
          C.devices.map(function (d) {
            return h('td', {}, C.sizes.map(function (size) {
              return h('label', { class: 'adm-check nowrap' },
                h('input', { type: 'checkbox', 'data-dev': d, 'data-size': size, checked: (p.sizes[d] || []).indexOf(size) >= 0 }), ' ' + size);
            }));
          }));
        var actions = h('td', {}, btn('Сохранить', '', function () {
          var sizes = {};
          C.devices.forEach(function (d) {
            sizes[d] = Array.prototype.map.call(tr.querySelectorAll('[data-dev="' + d + '"]:checked'), function (c) { return c.dataset.size; });
          });
          api('POST', '/api/admin/ads/placements', { key: p.key, page: p.page, label: label.value, enabled: enabled.checked, priority: Number(priority.value), sizes: sizes })
            .then(function (r) { render(r); ok('Место сохранено'); refreshPreview(); }).catch(fail('Ошибка: '));
        }));
        if (!p.builtin) actions.append(' ', btn('Удалить', 'danger', function () {
          api('POST', '/api/admin/ads/placements/' + encodeURIComponent(p.key) + '/delete', {}).then(render).catch(fail('Ошибка: '));
        }));
        tr.append(actions);
        return tr;
      }));
  }

  function buildPlacements() {
    el.placements = h('table', { class: 'adm-table' });
    var key = input({ placeholder: 'settings_bottom' }), page = input({ placeholder: 'secondary' });
    var add = btn('Добавить место', '', function () {
      api('POST', '/api/admin/ads/placements', { key: key.value.trim(), page: page.value.trim(), enabled: false, priority: 50,
        sizes: { phone: ['320x100'], tablet: ['728x90'], desktop: ['728x90'] } })
        .then(function (r) { render(r); ok('Место добавлено (выключено). Разметка: data-ad-placement в шаблоне страницы.'); }).catch(fail('Ошибка: '));
    });
    return section('placements', 'Места показа',
      h('p', { class: 'adm-note' }, 'Экран приложения запрашивает рекламный backend по ключу места, а backend сам выбирает материал. Места не перекрывают карточки слов, ответы и поля ввода; пустое место скрыто.'),
      ctx.wrap(el.placements),
      h('div', { class: 'adm-form' }, labeled('Ключ нового места', key), labeled('Страница', page), h('div', { class: 'adm-field' }, h('span', {}, ' '), add)));
  }

  // ------------------------------------------------------------ advertisers
  function renderAdvertisers(data) {
    [el.crAdv, el.linkAdv].forEach(function (sel) {
      var v = sel.value;
      sel.replaceChildren.apply(sel, data.advertisers.map(function (a) { return h('option', { value: a.id }, a.name + (a.awin_id ? ' #' + a.awin_id : '')); }));
      if (v) sel.value = v;
    });
    ctx.table(el.advertisers, ['Название', 'Awin advertiser ID', 'Membership', 'Вкл.', 'Страны', 'Языки', 'Темы', 'Регион', 'Last sync', ''],
      data.advertisers.map(function (a) {
        var st = a.membership_status;
        return h('tr', {},
          h('td', {}, a.name), h('td', { class: 'adm-num' }, a.awin_id || '—'),
          h('td', {}, badge(st, st === 'joined' ? 'ok' : st === 'rejected' || st === 'suspended' ? 'off' : 'warn')),
          h('td', {}, a.enabled ? '✓' : '—'), h('td', {}, ctx.list(a.countries) || '—'), h('td', {}, ctx.list(a.languages) || '—'),
          h('td', {}, ctx.list(a.topics) || '—'), h('td', {}, a.primary_region || '—'), h('td', { class: 'adm-num' }, ctx.fmtDateTime(a.synced_at)),
          h('td', { class: 'nowrap' }, btn('Изменить', '', function () { fillForm(el.advForm, a); }), ' ',
            a.awin_id ? btn('Проверить статус', '', function () {
              api('POST', '/api/admin/ads/awin/check/' + a.id, {})
                .then(function (r) { render(r); ok('Статус: ' + r.membership_status); })
                .catch(function (e) { ctx.flash('Awin: ' + e.message, 'err'); refreshState(); });
            }) : ''));
      }));
  }

  function buildAdvertisers() {
    el.awinState = h('div', { class: 'adm-row' });
    el.awinHint = h('p', { class: 'adm-note' });
    el.advertisers = h('table', { class: 'adm-table' });
    var rel = h('select', { class: 'adm-input' }, ['joined', 'pending', 'rejected', 'suspended', 'notjoined'].map(function (r) { return h('option', { value: r }, r); }));
    var country = input({ size: 3, maxlength: 2, placeholder: 'ES' });
    var sync = btn('Синхронизировать программы Awin', 'primary', function () {
      api('POST', '/api/admin/ads/awin/sync', { relationship: rel.value, country: country.value.trim() })
        .then(function (r) { render(r); ok('Синхронизировано программ (' + rel.value + '): ' + r.synced); })
        .catch(function (e) { ctx.flash('Awin: ' + e.message, 'err'); refreshState(); });
    });
    var importPreview = btn('Загрузить кандидатов (проверка Awin 2026-10-09)', '', function () {
      api('POST', '/api/admin/ads/import-preview', {})
        .then(function (r) { render(r); ok('Кандидаты загружены: ' + (r.imported || []).join(', ') + ' · режим ' + String(r.mode).toUpperCase()); refreshPreview(); })
        .catch(fail('Ошибка: '));
    });
    el.advForm = h('form', { class: 'adm-form' },
      h('input', { type: 'hidden', name: 'id' }),
      labeled('Название', input({ name: 'name', required: true })),
      labeled('Awin advertiser ID', input({ name: 'awin_id', inputmode: 'numeric' })),
      labeled('Страны (рынки)', input({ name: 'countries', placeholder: 'ES, PT' })),
      labeled('Языки', input({ name: 'languages', placeholder: 'es, pt' })),
      labeled('Темы', input({ name: 'topics', placeholder: 'language, books' })),
      h('label', { class: 'adm-check' }, h('input', { type: 'checkbox', name: 'enabled' }), ' Включён'),
      labeled('Заметки', input({ name: 'notes' }), true),
      h('div', { class: 'adm-row wide' }, h('button', { class: 'adm-btn primary', type: 'submit' }, 'Сохранить рекламодателя'),
        h('button', { class: 'adm-btn', type: 'reset' }, 'Очистить')));
    el.advForm.addEventListener('submit', function (ev) {
      ev.preventDefault();
      api('POST', '/api/admin/ads/advertisers', formData(el.advForm))
        .then(function (r) { render(r); el.advForm.reset(); ok('Рекламодатель сохранён'); }).catch(fail('Ошибка: '));
    });
    return section('awin', 'Awin и рекламодатели',
      el.awinState, el.awinHint,
      h('p', { class: 'adm-note' }, 'Программы (например, Trotec – Iberic, ID 115363) появляются здесь после синхронизации как обычные рекламодатели; статус membership приходит только из Awin API — вручную «joined» установить нельзя.'),
      h('div', { class: 'adm-row' }, h('span', {}, 'Relationship:'), rel, h('span', {}, 'Страна:'), country, sync, importPreview),
      ctx.wrap(el.advertisers),
      h('h3', { class: 'adm-subtitle' }, 'Рекламодатель вручную / изменение'), el.advForm);
  }

  // -------------------------------------------------------------- creatives
  function renderCreatives(data) {
    var advName = {};
    data.advertisers.forEach(function (a) { advName[a.id] = a.name; });
    ctx.table(el.creatives, ['#', 'Рекламодатель', 'Название', 'Тип', 'Размер', 'Image URL', 'Click URL', 'Текст (text ads)',
      'Страны / языки / темы', 'Период', 'Вкл.', 'Preview only', ''],
    data.creatives.map(function (c) {
      var enabled = h('input', { type: 'checkbox', checked: c.enabled });
      enabled.addEventListener('change', function () {
        api('POST', '/api/admin/ads/creatives/' + c.id + '/enabled', { enabled: enabled.checked })
          .then(function (r) { render(r); refreshPreview(); }).catch(fail('Ошибка: '));
      });
      return h('tr', {},
        h('td', { class: 'adm-num' }, c.id), h('td', {}, advName[c.advertiser_id] || c.advertiser_id), h('td', {}, c.name), h('td', {}, h('code', {}, c.kind)),
        h('td', { class: 'nowrap' }, c.width ? c.width + '×' + c.height : 'гибкий'),
        h('td', {}, h('code', { class: 'adm-raw' }, c.image_url || '—')),
        h('td', {}, h('code', { class: 'adm-raw' }, c.click_url || '—')),
        h('td', { class: 'adm-wrap-cell' }, c.kind === 'text' ? [h('strong', {}, c.headline || ''), c.body ? h('div', {}, c.body) : null, c.cta ? h('div', { class: 'adm-muted' }, 'CTA: ' + c.cta) : null] : '—'),
        h('td', {}, (ctx.list(c.countries) || '*') + ' / ' + (ctx.list(c.languages) || '*') + ' / ' + (ctx.list(c.topics) || '*')),
        h('td', { class: 'nowrap' }, (c.starts_on || '…') + ' — ' + (c.ends_on || '…')),
        h('td', {}, enabled),
        h('td', {}, c.preview_only ? badge('preview only', 'warn') : '—'),
        h('td', {}, btn('Изменить', '', function () { fillForm(el.crForm, c); syncKind(); })));
    }));
  }

  function kindField(kinds, label, node, wide) {
    var f = labeled(label, node, wide);
    f.dataset.kind = kinds;
    return f;
  }

  function buildCreatives() {
    el.creatives = h('table', { class: 'adm-table' });
    el.crAdv = h('select', { class: 'adm-input', name: 'advertiser_id' });
    el.crKind = h('select', { class: 'adm-input', name: 'kind' },
      h('option', { value: 'awin_html' }, 'Код Awin My Creative (awin_html)'),
      h('option', { value: 'image_link' }, 'Изображение + ссылка (image_link)'),
      h('option', { value: 'text' }, 'Текстовый (text)'));
    el.crKind.addEventListener('change', syncKind);
    el.crForm = h('form', { class: 'adm-form' },
      h('input', { type: 'hidden', name: 'id' }),
      labeled('Рекламодатель', el.crAdv), labeled('Тип', el.crKind), labeled('Название', input({ name: 'name' })),
      kindField('awin_html', 'Код My Creative', h('textarea', { class: 'adm-input adm-textarea adm-mono', name: 'raw_code',
        placeholder: '<a href="https://www.awin1.com/cread.php?..."><img src="https://www.awin1.com/cshow.php?..." width="728" height="90"></a>' }), true),
      kindField('image_link text', 'Ссылка (awin1.com / tidd.ly)', input({ name: 'click_url' })),
      kindField('image_link', 'URL изображения', input({ name: 'image_url' })),
      kindField('image_link', 'Ширина', input({ name: 'width', inputmode: 'numeric' })),
      kindField('image_link', 'Высота', input({ name: 'height', inputmode: 'numeric' })),
      kindField('image_link', 'Alt', input({ name: 'alt' })),
      kindField('text', 'Заголовок (headline)', input({ name: 'headline', maxlength: '80' })),
      kindField('text', 'Текст (body)', input({ name: 'body', maxlength: '160' })),
      kindField('text', 'Кнопка (CTA)', input({ name: 'cta', maxlength: '30' })),
      labeled('Страны', input({ name: 'countries', placeholder: 'пусто = как у рекламодателя' })),
      labeled('Языки', input({ name: 'languages' })),
      labeled('Темы', input({ name: 'topics' })),
      labeled('С даты', input({ type: 'date', name: 'starts_on' })),
      labeled('По дату', input({ type: 'date', name: 'ends_on' })),
      h('label', { class: 'adm-check' }, h('input', { type: 'checkbox', name: 'enabled' }), ' Включён'),
      h('label', { class: 'adm-check' }, h('input', { type: 'checkbox', name: 'preview_only' }), ' Только предпросмотр (неофициальный текст, никогда в LIVE)'),
      h('div', { class: 'adm-row wide' }, h('button', { class: 'adm-btn primary', type: 'submit' }, 'Сохранить материал'),
        h('button', { class: 'adm-btn', type: 'reset' }, 'Очистить')));
    el.crForm.addEventListener('submit', function (ev) {
      ev.preventDefault();
      api('POST', '/api/admin/ads/creatives', formData(el.crForm))
        .then(function (r) { render(r); el.crForm.reset(); syncKind(); ok('Материал сохранён'); refreshPreview(); })
        .catch(fail('Материал отклонён: '));
    });
    el.crForm.addEventListener('reset', function () { setTimeout(syncKind, 0); });

    el.linkAdv = h('select', { class: 'adm-input' });
    var dest = input({}), ref = input({ placeholder: 'dashboard_bottom' }), cr = input({ inputmode: 'numeric' });
    var out = h('div', { class: 'adm-note' });
    var go = btn('Создать ссылку', '', function () {
      api('POST', '/api/admin/ads/awin/link', { advertiser_id: el.linkAdv.value, destination_url: dest.value.trim(),
        clickref: ref.value.trim(), creative_id: cr.value.trim() || null })
        .then(function (r) { render(r); out.textContent = r.url; ok('Ссылка создана'); })
        .catch(function (e) { ctx.flash('Awin: ' + e.message, 'err'); refreshState(); });
    });
    return section('creatives', 'Материалы (creatives)',
      h('p', { class: 'adm-note' }, 'Код из Awin → My Creative вставляется как текст: сервер сохраняет только ссылку awin1.com, изображение и размер. Скрипты, iframe, стили и обработчики событий отклоняются. Поддерживаемые размеры: 320×50, 320×100, 300×250, 728×90, 970×250.'),
      ctx.wrap(el.creatives), h('h3', { class: 'adm-subtitle' }, 'Новый материал / изменение'), el.crForm,
      h('h3', { class: 'adm-subtitle' }, 'Партнёрская ссылка (Link Builder)'),
      h('p', { class: 'adm-note' }, 'Создаётся только по кнопке и только для программ со статусом joined. clickref — лишь ключ места, без данных пользователя.'),
      h('div', { class: 'adm-form' }, labeled('Рекламодатель', el.linkAdv), labeled('Целевая страница (https, необязательно)', dest),
        labeled('clickref (ключ места)', ref), labeled('Записать в материал #', cr), h('div', { class: 'adm-field' }, h('span', {}, ' '), go)),
      out);
  }

  function syncKind() {
    var kind = el.crKind.value;
    el.crForm.querySelectorAll('[data-kind]').forEach(function (n) { n.hidden = n.dataset.kind.split(' ').indexOf(kind) < 0; });
  }
  function fillForm(form, item) {
    form.reset();
    Object.keys(item).forEach(function (k) {
      var field = form.elements[k];
      if (!field || !field.type) return;
      var v = item[k];
      if (field.type === 'checkbox') field.checked = !!v;
      else field.value = Array.isArray(v) ? v.join(', ') : (v == null ? '' : v);
    });
    form.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
  function formData(form) {
    var out = {};
    Array.prototype.forEach.call(form.elements, function (f) {
      if (!f.name) return;
      out[f.name] = f.type === 'checkbox' ? f.checked : f.value;
    });
    if (!out.id) delete out.id;
    return out;
  }

  // ---------------------------------------------------------------- preview
  function renderSimButtons(data) {
    el.simButtons.forEach(function (b) { b.classList.toggle('is-current', (b.dataset.sim === 'exit' ? '' : b.dataset.sim) === (data.preview_plan || '')); });
    el.deviceButtons.forEach(function (b) { b.classList.toggle('is-current', b.dataset.device === sim.device); });
  }

  function buildPreview() {
    el.simButtons = [['free', 'Free'], ['premium', 'Premium'], ['family', 'Family'], ['exit', 'Выйти из симуляции']].map(function (p) {
      var b = btn(p[1], '', function () {
        api('POST', '/api/admin/plan-preview', { plan: p[0] })
          .then(refreshState).then(refreshPreview)
          .then(function () { ok(p[0] === 'exit' ? 'Симуляция выключена' : 'Симуляция тарифа: ' + p[1]); })
          .catch(fail('Ошибка: '));
      });
      b.dataset.sim = p[0];
      return b;
    });
    el.deviceButtons = [['phone', 'Телефон'], ['tablet', 'Планшет'], ['desktop', 'Компьютер']].map(function (d) {
      var b = btn(d[1], '', function () { sim.device = d[0]; renderSimButtons(state || {}); refreshPreview(); });
      b.dataset.device = d[0];
      return b;
    });
    el.page = h('select', { class: 'adm-input' }, h('option', { value: 'dashboard' }, 'Главная (/)'), h('option', { value: 'secondary' }, 'База слов'));
    el.page.addEventListener('change', refreshPreview);
    el.country = input({ size: 3, maxlength: 2, placeholder: 'NL' });
    el.lang = input({ size: 3, maxlength: 2, placeholder: 'ru' });
    el.frame = h('iframe', { title: 'Предпросмотр страницы приложения', referrerpolicy: 'no-referrer' });
    el.device = h('div', { class: 'adm-device' }, el.frame);
    el.sim = h('div', {});
    el.previewCard = section('preview', 'Предпросмотр для FREE пользователя',
      h('p', { class: 'adm-note' }, 'Симуляция тарифа хранится только в вашей сессии: подписка, права и данные не меняются. Предпросмотр показывает только макеты — без загрузки изображений рекламодателей, ссылок, показов и кликов; в статистику LIVE он не попадает и режим LIVE не включает.'),
      h('div', { class: 'adm-row' }, h('span', {}, 'Тариф:'), el.simButtons),
      h('div', { class: 'adm-row' }, h('span', {}, 'Устройство:'), el.deviceButtons, h('span', {}, 'Страница:'), el.page,
        h('span', {}, 'Страна:'), el.country, h('span', {}, 'Язык:'), el.lang, btn('Обновить', '', refreshPreview)),
      h('div', { class: 'adm-preview-stage' }, h('div', { class: 'adm-device-wrap' }, el.device),
        h('div', { class: 'adm-sim-list' }, h('strong', {}, 'Подбор для Free (макеты):'), el.sim)));
    return el.previewCard;
  }

  function refreshPreview() {
    if (!state || el.previewCard.offsetParent === null) return;
    var width = WIDTHS[sim.device];
    var avail = Math.max(300, el.previewCard.clientWidth - 380);
    var scale = Math.min(1, avail / (width + 20));
    var height = sim.device === 'phone' ? 760 : 900;
    el.frame.style.width = width + 'px'; el.frame.style.height = height + 'px';
    el.frame.style.transform = 'scale(' + scale + ')';
    el.device.style.width = (width * scale) + 'px'; el.device.style.height = (height * scale) + 'px';
    el.frame.src = ctx.APP_ORIGIN + (el.page.value === 'secondary' ? '/word-database' : '/') + '?ads_preview=' + Date.now();
    var params = new URLSearchParams({ plan: 'free', page: el.page.value, device: sim.device,
      country: el.country.value.trim(), lang: el.lang.value.trim() });
    api('GET', '/api/admin/ads/simulate?' + params).then(function (r) {
      el.sim.replaceChildren();
      if (!r.slots.length) { el.sim.append(h('p', { class: 'adm-note' }, 'Нет подходящих материалов — место скрыто.')); return; }
      r.slots.forEach(function (slot) {
        el.sim.append(h('div', { class: 'adm-note' }, slot.placement + ' · ' + slot.size + ' · ' + slot.render), mockSlot(slot));
      });
    }).catch(fail('Предпросмотр: '));
  }

  function mockSlot(slot) {
    return h('aside', { class: 'ad-slot ad-slot--filled ad-slot--preview', 'data-ad-size': slot.size,
      style: '--ad-w:' + slot.width + 'px;--ad-h:' + slot.height + 'px' },
    h('span', { class: 'ad-slot__label' }, slot.label),
    h('div', { class: 'ad-slot__frame' }, h('div', { class: 'ad-slot__card ad-tone--' + (slot.tone || 'violet') },
      h('div', { class: 'ad-slot__copy' }, h('strong', { class: 'ad-slot__headline' }, slot.headline),
        slot.body ? h('span', { class: 'ad-slot__body' }, slot.body) : null,
        h('span', { class: 'ad-slot__advertiser' }, (slot.advertiser || '') + ' · ' + slot.size)),
      slot.cta ? h('span', { class: 'ad-slot__cta' }, slot.cta) : null)));
  }

  // ------------------------------------------------------------------ stats
  function buildStats() {
    el.stats = h('table', { class: 'adm-table' });
    el.days = h('select', { class: 'adm-input' }, [7, 30, 90, 365].map(function (d) { return h('option', { value: d, selected: d === 30 }, d + ' дней'); }));
    el.days.addEventListener('change', loadStats);
    el.report = h('table', { class: 'adm-table' });
    el.repStart = input({ type: 'date' }); el.repEnd = input({ type: 'date' });
    el.repRegion = h('select', { class: 'adm-input' });
    var go = btn('Загрузить отчёт Awin', '', function () {
      api('POST', '/api/admin/ads/awin/report', { start: el.repStart.value, end: el.repEnd.value, region: el.repRegion.value })
        .then(function (r) {
          ctx.table(el.report, ['Материал', 'Рекламодатель', 'Регион', 'Показы', 'Клики', 'Транзакции', 'Сумма', 'Комиссия'], r.rows.map(function (x) {
            return h('tr', {}, h('td', {}, (x.creativeId || '') + ' ' + (x.creativeName || '')), h('td', {}, x.advertiserName), h('td', {}, x.region || '—'),
              h('td', { class: 'adm-num' }, x.impressions), h('td', { class: 'adm-num' }, x.clicks), h('td', { class: 'adm-num' }, x.totalNo),
              h('td', { class: 'adm-num' }, (x.totalValue == null ? '' : x.totalValue) + ' ' + (x.currency || '')), h('td', { class: 'adm-num' }, x.totalComm));
          }));
        })
        .catch(function (e) { ctx.flash('Awin: ' + e.message, 'err'); refreshState(); });
    });
    return section('stats', 'Статистика (анонимно)',
      h('p', { class: 'adm-note' }, 'Только агрегированные счётчики LIVE-показов: без User ID и без данных пользователя. Предпросмотр, администраторы и платные пользователи не учитываются. Платформа (Web / Telegram / Android) в счётчиках не хранится — доступны место, материал, устройство и страна.'),
      h('div', { class: 'adm-row' }, h('span', {}, 'Период:'), el.days),
      ctx.wrap(el.stats),
      h('h3', { class: 'adm-subtitle' }, 'Отчёт Awin по материалам'),
      h('div', { class: 'adm-form' }, labeled('С', el.repStart), labeled('По', el.repEnd), labeled('Регион', el.repRegion), h('div', { class: 'adm-field' }, h('span', {}, ' '), go)),
      ctx.wrap(el.report));
  }

  function loadStats() {
    api('GET', '/api/admin/ads/stats?days=' + encodeURIComponent(el.days.value)).then(function (r) {
      ctx.table(el.stats, ['Рекламодатель', 'Материал', 'Место', 'Устройство', 'Страна', 'Период', 'Показы', 'Клики', 'CTR'], r.rows.map(function (x) {
        return h('tr', {}, h('td', {}, x.advertiser_name || '—'), h('td', {}, '#' + x.creative_id + ' ' + x.creative_name), h('td', {}, h('code', {}, x.placement)),
          h('td', {}, x.device || '—'), h('td', {}, x.country || '—'), h('td', { class: 'nowrap' }, x.first_day + ' — ' + x.last_day),
          h('td', { class: 'adm-num' }, ctx.num(x.impressions)), h('td', { class: 'adm-num' }, ctx.num(x.clicks)),
          h('td', { class: 'adm-num' }, x.impressions ? (100 * x.clicks / x.impressions).toFixed(2) + '%' : '—'));
      }));
    }).catch(fail('Статистика: '));
  }

  // -------------------------------------------------------------------- log
  function renderLog(data) {
    ctx.table(el.log, ['Время', 'Операция', 'HTTP', 'Результат', 'Сообщение'], (data.api_log || []).map(function (r) {
      return h('tr', {}, h('td', { class: 'nowrap' }, ctx.fmtDateTime(r.at)), h('td', {}, r.operation), h('td', { class: 'adm-num' }, r.http_status || '—'),
        h('td', {}, badge(r.ok ? 'ok' : 'ошибка', r.ok ? 'ok' : 'off')), h('td', { class: 'adm-wrap-cell' }, r.message));
    }));
  }

  function refreshState() {
    return api('GET', '/api/admin/ads/state').then(render).catch(fail('Реклама: '));
  }

  PLAdmin.register('ads', {
    mount: function (panel, c) {
      ctx = c; h = c.h;
      el.log = h('table', { class: 'adm-table' });
      var jump = h('nav', { class: 'adm-subnav', 'aria-label': 'Разделы рекламы' },
        [['settings', 'Общие настройки'], ['awin', 'Awin и рекламодатели'], ['creatives', 'Материалы'], ['placements', 'Места показа'],
          ['preview', 'Предпросмотр'], ['stats', 'Статистика'], ['log', 'Журнал API']].map(function (s) {
          return h('a', { href: '#ads-' + s[0] }, s[1]);
        }));
      panel.append(jump, buildSettings(), buildAdvertisers(), buildCreatives(), buildPlacements(), buildPreview(), buildStats(),
        section('log', 'Журнал Awin API', ctx.wrap(el.log)));
      syncKind();
      refreshState().then(function () { refreshPreview(); loadStats(); });
      window.addEventListener('resize', function () { clearTimeout(el.resizeTimer); el.resizeTimer = setTimeout(refreshPreview, 300); });
    },
    show: function () { refreshState().then(function () { refreshPreview(); loadStats(); }); }
  });
})();
