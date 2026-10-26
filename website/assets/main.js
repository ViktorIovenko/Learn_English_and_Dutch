/* ParallelLingvo — shared header/theme/dropdown behavior (vanilla JS, no dependencies) */
(function () {
  'use strict';

  var LOGO_LIGHT = '/assets/new-logo-full.png';
  var LOGO_DARK = '/assets/new-logo-full-dark.png';
  var FOOTER_LOGO_LIGHT = '/assets/logo-wordmark.png';
  var FOOTER_LOGO_DARK = '/assets/logo-wordmark-dark.png';
  // The marketing site is always served from parallellingvo.app; the product
  // itself (and its session) lives on this subdomain.
  var AUTH_ORIGIN = 'https://app.parallellingvo.app';

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.querySelectorAll('.js-theme-icon').forEach(function (el) {
      el.textContent = theme === 'dark' ? '☀' : '☾';
    });
    document.querySelectorAll('.js-logo').forEach(function (img) {
      img.src = theme === 'dark' ? LOGO_DARK : LOGO_LIGHT;
    });
    document.querySelectorAll('.js-footer-logo').forEach(function (img) {
      img.src = theme === 'dark' ? FOOTER_LOGO_DARK : FOOTER_LOGO_LIGHT;
    });
    document.dispatchEvent(new CustomEvent('pl-theme-change', { detail: { theme: theme } }));
  }

  function getStoredTheme() {
    try {
      return localStorage.getItem('pl-theme');
    } catch (e) {
      return null;
    }
  }

  function setStoredTheme(theme) {
    try {
      localStorage.setItem('pl-theme', theme);
    } catch (e) {}
  }

  function initTheme() {
    var stored = getStoredTheme();
    var theme = stored === 'dark' || stored === 'light'
      ? stored
      : (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    applyTheme(theme);
  }

  function toggleTheme() {
    var current = document.documentElement.getAttribute('data-theme') || 'light';
    var next = current === 'dark' ? 'light' : 'dark';
    setStoredTheme(next);
    applyTheme(next);
  }

  // Generic dropdown/menu handling: any element with [data-toggle="menuId"]
  // toggles the [hidden] attribute of #menuId, closes on outside click / Escape,
  // and closes other open menus first.
  function closeAllMenus(except) {
    document.querySelectorAll('[data-menu]').forEach(function (menu) {
      if (menu !== except) menu.hidden = true;
    });
  }

  function initDropdowns() {
    document.addEventListener('click', function (e) {
      var toggle = e.target.closest('[data-toggle]');
      if (toggle) {
        var id = toggle.getAttribute('data-toggle');
        var menu = document.getElementById(id);
        if (menu) {
          var willOpen = menu.hidden;
          closeAllMenus(willOpen ? menu : null);
          menu.hidden = !willOpen;
        }
        e.stopPropagation();
        return;
      }
      if (!e.target.closest('[data-menu]')) closeAllMenus();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeAllMenus();
    });
  }

  // "Continue with Google" / "Continue with Telegram" open their auth flow
  // in a small popup instead of navigating the whole tab away, so the
  // visitor never leaves this page. The popup is opened directly on the app
  // backend's own origin (not via the marketing site's /auth/* -> 302
  // redirect) so the session cookie set at the start of the flow and the one
  // read back at the callback belong to the same top-level navigation, with
  // no extra hop for a browser to lose it across. On success we do NOT
  // navigate anywhere — the visitor stays on the marketing site and the
  // header switches to "Open app" / "Log out"; where they go next is their
  // own choice, made through the "Open app" picker (Android/iOS/Telegram/Web).
  function openAuthPopup(provider, path, next) {
    var w = 480, h = 640;
    var left = Math.max(0, (window.screen.width - w) / 2);
    var top = Math.max(0, (window.screen.height - h) / 2);
    var url = AUTH_ORIGIN + path + '?popup=1' + (next ? '&next=' + encodeURIComponent(next) : '');
    var popup = window.open(
      url,
      'plg-' + provider + '-login',
      'width=' + w + ',height=' + h + ',left=' + left + ',top=' + top + ',resizable=yes,scrollbars=yes'
    );
    if (!popup) {
      // Popup blocked — fall back to a normal full-page redirect.
      window.location.href = url.replace('popup=1&', '').replace('?popup=1', '');
      return;
    }
    function onMessage(e) {
      // The popup runs on AUTH_ORIGIN while this page is on the marketing
      // site's own origin — they're never the same, so we validate against
      // the one origin the popup can legitimately send from instead of
      // comparing to window.location.origin.
      if (e.origin !== AUTH_ORIGIN) return;
      var data = e.data || {};
      if (data.source !== 'parallellingvo-auth' || data.provider !== provider) return;
      window.removeEventListener('message', onMessage);
      if (data.ok) initAuthState();
    }
    window.addEventListener('message', onMessage);
  }

  var OPEN_APP_STRINGS = {
    en: { open: 'Open app', logout: 'Log out', admin: 'Админ', android: 'Android', ios: 'iOS — coming soon', telegram: 'Telegram', web: 'Web' },
    ru: { open: 'Открыть приложение', logout: 'Выйти', admin: 'Админ', android: 'Android', ios: 'iOS — скоро', telegram: 'Telegram', web: 'Веб' }
  };
  var ANDROID_URL = 'https://play.google.com/store/apps/details?id=app.parallellingvo';
  // Temporary: "?start=login" opens the bot chat and runs /start login,
  // which sends a message with an "Open app" button the visitor taps
  // themselves — instead of "?startapp=login", which launches the Mini App
  // immediately (unstyled for Telegram's theme, looks like a plain website;
  // see conversation notes). Switch back to startapp once that Mini App
  // theming work is done.
  var TELEGRAM_APP_URL = 'https://t.me/parallellingvo_bot?start=login';
  var openAppCounter = 0;

  // Ask the app backend (shared session cookie across *.parallellingvo.app)
  // whether the visitor is already signed in, and if so swap every
  // Log in / Sign up dropdown for an "Open app" / "Log out" pair. "Open app"
  // is itself a dropdown: the visitor picks Android / iOS / Telegram / Web
  // and only then actually leaves the marketing site.
  function initAuthState() {
    fetch(AUTH_ORIGIN + '/auth/status', { credentials: 'include' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data || !data.authenticated) return;
        var t = OPEN_APP_STRINGS[document.documentElement.lang] || OPEN_APP_STRINGS.en;
        var containers = [];
        document.querySelectorAll('.js-google-login').forEach(function (link) {
          var dropdown = link.closest('.dropdown');
          var container = dropdown && dropdown.parentElement;
          if (container && containers.indexOf(container) === -1) containers.push(container);
        });
        containers.forEach(function (container) {
          var dropdowns = Array.prototype.filter.call(container.children, function (el) {
            return el.classList && el.classList.contains('dropdown') && el.querySelector('.js-google-login');
          });
          if (!dropdowns.length) return;
          var trigger = dropdowns[dropdowns.length - 1].querySelector('[data-toggle]');
          var cls = trigger ? trigger.className : 'btn btn-purple';
          var style = trigger ? (trigger.getAttribute('style') || '') : '';
          var menuId = 'openapp-menu-' + (++openAppCounter);
          var widget = document.createElement('span');
          widget.className = 'js-auth-widget dropdown';
          widget.innerHTML =
            '<button type="button" class="' + cls + '" style="' + style + '" data-toggle="' + menuId + '">' + t.open + ' <span class="caret">▾</span></button>' +
            '<div id="' + menuId + '" class="dropdown-panel top-right" data-menu hidden>' +
            '<a class="dropdown-item link" href="' + ANDROID_URL + '" target="_blank" rel="noopener">' + t.android + '</a>' +
            '<span class="dropdown-item link is-disabled" aria-disabled="true">' + t.ios + '</span>' +
            '<a class="dropdown-item link" href="' + TELEGRAM_APP_URL + '" target="_blank" rel="noopener">' + t.telegram + '</a>' +
            '<a class="dropdown-item link" href="' + AUTH_ORIGIN + '/" target="_blank" rel="noopener">' + t.web + '</a>' +
            '</div>' +
            // "Admin" only when the backend itself confirmed is_admin (ADMIN_IDS /
            // ADMIN_EMAILS). It is just a shortcut: /admin and every /api/admin/*
            // call re-check the session on the server.
            (data.is_admin === true ? '<a class="btn btn-outline js-admin-link" href="/admin/">' + t.admin + '</a>' : '') +
            '<button type="button" class="btn btn-outline js-logout">' + t.logout + '</button>';
          dropdowns[0].replaceWith(widget);
          dropdowns.slice(1).forEach(function (d) { d.remove(); });
        });
      })
      .catch(function () {});
  }

  // Logging out is a cross-origin fetch (not a navigation) so the visitor
  // stays on whichever marketing-site page they clicked it from, same as
  // the login popup never leaving this page.
  function initLogout() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('.js-logout');
      if (!btn) return;
      btn.disabled = true;
      fetch(AUTH_ORIGIN + '/auth/logout', { credentials: 'include' })
        .catch(function () {})
        .then(function () { window.location.reload(); });
    });
  }

  // Mobile hamburger menu: toggles a class on the enclosing .site-header rather
  // than reusing the [data-menu] dropdown system, so opening "Log in"/"Sign up"
  // inside the panel doesn't also close the panel itself.
  function initMobileMenu() {
    document.querySelectorAll('.mobile-menu-btn').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        var header = btn.closest('.site-header');
        if (!header) return;
        var open = header.classList.toggle('mobile-open');
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    });
    document.addEventListener('click', function (e) {
      var header = document.querySelector('.site-header.mobile-open');
      if (!header) return;
      if (header.contains(e.target)) return;
      header.classList.remove('mobile-open');
      var btn = header.querySelector('.mobile-menu-btn');
      if (btn) btn.setAttribute('aria-expanded', 'false');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      var header = document.querySelector('.site-header.mobile-open');
      if (!header) return;
      header.classList.remove('mobile-open');
      var btn = header.querySelector('.mobile-menu-btn');
      if (btn) btn.setAttribute('aria-expanded', 'false');
    });
    // Following a same-page anchor link (#demo, #faq, ...) should close the panel.
    document.querySelectorAll('.site-header-collapsible .main-nav a[href*="#"]').forEach(function (a) {
      a.addEventListener('click', function () {
        var header = a.closest('.site-header');
        if (header) header.classList.remove('mobile-open');
      });
    });
  }

  function initGoogleAuth() {
    document.addEventListener('click', function (e) {
      var link = e.target.closest('.js-google-login');
      if (!link) return;
      e.preventDefault();
      openAuthPopup('google', '/auth/google', link.getAttribute('data-next') || '/upload');
    });
  }

  // "Continue with Telegram" — same popup pattern as Google, via Telegram's
  // OAuth 2.0 / OIDC login (oauth.telegram.org, configured through
  // BotFather's "Login Widget" settings: Client ID/Secret + redirect URI
  // https://app.parallellingvo.app/auth/telegram/callback). /auth/telegram
  // already supports ?popup=1 the same way /auth/google does.
  function initTelegramAuth() {
    document.addEventListener('click', function (e) {
      var link = e.target.closest('.js-telegram-login');
      if (!link) return;
      e.preventDefault();
      openAuthPopup('telegram', '/auth/telegram', link.getAttribute('data-next') || '/upload');
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTheme();
    initDropdowns();
    initMobileMenu();
    initGoogleAuth();
    initTelegramAuth();
    initLogout();
    initAuthState();
    document.querySelectorAll('.js-theme-toggle').forEach(function (btn) {
      btn.addEventListener('click', toggleTheme);
    });
  });
})();
