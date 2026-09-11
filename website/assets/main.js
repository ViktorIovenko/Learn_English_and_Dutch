/* ParallelLingvo — shared header/theme/dropdown behavior (vanilla JS, no dependencies) */
(function () {
  'use strict';

  var LOGO_LIGHT = '/assets/new-logo-full.png';
  var LOGO_DARK = '/assets/new-logo-full-dark.png';
  var FOOTER_LOGO_LIGHT = '/assets/logo-wordmark.png';
  var FOOTER_LOGO_DARK = '/assets/logo-wordmark-dark.png';

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

  document.addEventListener('DOMContentLoaded', function () {
    initTheme();
    initDropdowns();
    document.querySelectorAll('.js-theme-toggle').forEach(function (btn) {
      btn.addEventListener('click', toggleTheme);
    });
  });
})();
