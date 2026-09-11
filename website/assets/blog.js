/* ParallelLingvo — blog index search / sort / tag filter (vanilla JS) */
(function () {
  'use strict';

  var root = document.getElementById('blog-index');
  if (!root) return;

  var LANG = (document.documentElement.lang === 'ru') ? 'ru' : 'en';
  var isRu = LANG === 'ru';
  var langPrefix = isRu ? 'ru/' : '';

  var ARTICLES = [
    { id: "parallel-method", slug: "parallel-method", category: "Языки", categoryEn: "Languages", title: "Как работает метод параллельного изучения", titleEn: "How the parallel learning method works", excerpt: "Одно слово открывает дверь сразу в несколько языков — разбираем механику.", excerptEn: "One word opens the door to several languages at once — the mechanics.", date: "2026-09-11", dateLabel: "11 сент. 2026 г.", dateLabelEn: "Sep 11, 2026", readTime: "6", readTimeEn: "6", tags: ["Languages","Learning","Tips"] }
  ];

  var allTags = Array.prototype.concat.apply([], ARTICLES.map(function (a) { return a.tags; }))
    .filter(function (t, i, arr) { return arr.indexOf(t) === i; });

  var sortLabels = isRu
    ? { newest: 'Сначала новые', oldest: 'Сначала старые', title: 'По названию' }
    : { newest: 'Newest first', oldest: 'Oldest first', title: 'By title' };

  var state = { query: '', sort: 'newest', activeTags: [] };

  var searchInput = root.querySelector('.js-blog-search');
  var sortBtn = root.querySelector('.js-blog-sort-btn');
  var sortLabelEl = root.querySelector('.js-blog-sort-label');
  var sortPanel = document.getElementById('blog-sort-panel');
  var tagRow = root.querySelector('.js-blog-tags');
  var grid = root.querySelector('.js-blog-grid');
  var emptyState = root.querySelector('.js-blog-empty');

  function buildSortPanel() {
    sortPanel.innerHTML = '';
    ['newest', 'oldest', 'title'].forEach(function (key) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'sort-opt' + (state.sort === key ? ' active' : '');
      btn.innerHTML = sortLabels[key] + '<span class="sort-check">✓</span>';
      btn.addEventListener('click', function () {
        state.sort = key;
        sortPanel.hidden = true;
        render();
      });
      sortPanel.appendChild(btn);
    });
  }

  function buildTagRow() {
    tagRow.innerHTML = '';
    allTags.forEach(function (tag) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'tag-chip' + (state.activeTags.indexOf(tag) !== -1 ? ' active' : '');
      btn.textContent = tag;
      btn.addEventListener('click', function () {
        var i = state.activeTags.indexOf(tag);
        if (i === -1) state.activeTags.push(tag); else state.activeTags.splice(i, 1);
        render();
      });
      tagRow.appendChild(btn);
    });
  }

  function render() {
    var q = state.query.trim().toLowerCase();
    var list = ARTICLES.filter(function (a) {
      var title = isRu ? a.title : a.titleEn;
      var excerpt = isRu ? a.excerpt : a.excerptEn;
      var matchesQuery = !q || title.toLowerCase().indexOf(q) !== -1 || excerpt.toLowerCase().indexOf(q) !== -1;
      var matchesTags = state.activeTags.length === 0 || state.activeTags.every(function (t) { return a.tags.indexOf(t) !== -1; });
      return matchesQuery && matchesTags;
    });
    list = list.slice().sort(function (x, y) {
      if (state.sort === 'oldest') return x.date < y.date ? -1 : x.date > y.date ? 1 : 0;
      if (state.sort === 'title') {
        var xt = isRu ? x.title : x.titleEn, yt = isRu ? y.title : y.titleEn;
        return xt.localeCompare(yt);
      }
      return x.date < y.date ? 1 : x.date > y.date ? -1 : 0;
    });

    sortLabelEl.textContent = sortLabels[state.sort];
    buildSortPanel();
    buildTagRow();

    grid.innerHTML = '';
    if (list.length === 0) {
      grid.hidden = true;
      emptyState.hidden = false;
    } else {
      grid.hidden = false;
      emptyState.hidden = true;
      list.forEach(function (a) {
        var url = 'https://parallellingvo.app/' + langPrefix + 'blog/' + a.slug + '/';
        var card = document.createElement('a');
        card.href = url;
        card.className = 'article-card';
        var img = document.createElement('img');
        img.src = '/assets/blog-placeholder.svg';
        img.alt = isRu ? 'Изображение статьи' : 'Article image';
        img.loading = 'lazy';
        var body = document.createElement('div');
        body.className = 'article-card-body';
        body.innerHTML =
          '<div class="article-cat">' + (isRu ? a.category : a.categoryEn) + '</div>' +
          '<h2>' + (isRu ? a.title : a.titleEn) + '</h2>' +
          '<p>' + (isRu ? a.excerpt : a.excerptEn) + '</p>' +
          '<div class="article-meta"><span>' + (isRu ? a.dateLabel : a.dateLabelEn) + '</span><span>·</span><span>' + (isRu ? a.readTime + ' чтения' : a.readTimeEn + ' read') + '</span></div>';
        card.appendChild(img);
        card.appendChild(body);
        grid.appendChild(card);
      });
    }
  }

  searchInput.addEventListener('input', function () { state.query = searchInput.value; render(); });
  sortBtn.addEventListener('click', function () { sortPanel.hidden = !sortPanel.hidden; });

  render();
})();
