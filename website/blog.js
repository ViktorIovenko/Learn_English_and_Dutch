/* ParallelLingvo — blog index search / sort / tag filter (vanilla JS) */
(function () {
  'use strict';

  var root = document.getElementById('blog-index');
  if (!root) return;

  var LANG = (document.documentElement.lang === 'ru') ? 'ru' : 'en';
  var isRu = LANG === 'ru';
  var langPrefix = isRu ? 'ru/' : '';

  var ARTICLES = [
    { id: "learn-languages-through-a-regular-daily-practice-9b0280e5", slug: "learn-languages-through-a-regular-daily-practice-9b0280e5", category: "Tips", categoryEn: "Tips", title: "Learn Languages Through a Regular Daily Practice", titleEn: "Learn Languages Through a Regular Daily Practice", excerpt: "Learning a language becomes easier when practice is regular and focused.\\n\\nShort daily sessions help build a habit, remember new words, and notice steady progress. ParallelLingvo supports a calm routine for learning several languages without overload.", excerptEn: "Learning a language becomes easier when practice is regular and focused.\\n\\nShort daily sessions help build a habit, remember new words, and notice steady progress. ParallelLingvo supports a calm routine for learning several languages without overload.", date: "2026-09-29", dateLabel: "29 сент. 2026 г.", dateLabelEn: "Sep 29, 2026", readTime: "1", readTimeEn: "1", image: "", tags: ["Tips"] },
    { id: "regular-practice-makes-language-learning-easier-080ba18d", slug: "regular-practice-makes-language-learning-easier-080ba18d", category: "Tips", categoryEn: "Tips", title: "Regular Practice Makes Language Learning Easier", titleEn: "Regular Practice Makes Language Learning Easier", excerpt: "Regular practice makes language learning clearer and more sustainable.\\n\\nA short daily routine helps learners remember new words, stay motivated, and see progress over time.", excerptEn: "Regular practice makes language learning clearer and more sustainable.\\n\\nA short daily routine helps learners remember new words, stay motivated, and see progress over time.", date: "2026-09-29", dateLabel: "29 сент. 2026 г.", dateLabelEn: "Sep 29, 2026", readTime: "1", readTimeEn: "1", image: "/assets/blog/regular-practice-makes-language-learning-easier-080ba18d.png", tags: ["Tips"] },
    { id: "test-parallellingvo-telegram-b91fb40e", slug: "test-parallellingvo-telegram-b91fb40e", category: "Tips", categoryEn: "Tips", title: "Test ParallelLingvo Telegram", titleEn: "Test ParallelLingvo Telegram", excerpt: "# Test article This is a test article for ParallelLingvo publication.", excerptEn: "# Test article This is a test article for ParallelLingvo publication.", date: "2026-09-29", dateLabel: "29 сент. 2026 г.", dateLabelEn: "Sep 29, 2026", readTime: "1", readTimeEn: "1", image: "", tags: ["Tips"] },
    { id: "how-to-learn-multiple-languages-at-the-same-time-without-mix-e496c345", slug: "how-to-learn-multiple-languages-at-the-same-time-without-mix-e496c345", category: "Tips", categoryEn: "Tips", title: "How to Learn Multiple Languages at the Same Time Without Mixing Them Up", titleEn: "How to Learn Multiple Languages at the Same Time Without Mixing Them Up", excerpt: "# How to Learn Multiple Languages at the Same Time Without Mixing Them Up Learning two or three languages at the same time can feel confusing at first. Similar words start competing with each other, vocabulary gets stored in separate notebooks or apps, and switching between languages requires con...", excerptEn: "# How to Learn Multiple Languages at the Same Time Without Mixing Them Up Learning two or three languages at the same time can feel confusing at first. Similar words start competing with each other, vocabulary gets stored in separate notebooks or apps, and switching between languages requires con...", date: "2026-09-28", dateLabel: "28 сент. 2026 г.", dateLabelEn: "Sep 28, 2026", readTime: "5", readTimeEn: "5", image: "/assets/blog/how-to-learn-multiple-languages-at-the-same-time-without-mix-e496c345.png", tags: ["Tips"] },
    { id: "parallellingvo-2eba354a", slug: "parallellingvo-2eba354a", category: "Tips", categoryEn: "Tips", title: "Тестовый пост ParallelLingvo", titleEn: "Тестовый пост ParallelLingvo", excerpt: "🧪 Тестовая публикация ParallelLingvo Проверяем работу автоматической публикации через новую систему. Если вы видите этот пост — значит, всё работает корректно. ✅", excerptEn: "🧪 Тестовая публикация ParallelLingvo Проверяем работу автоматической публикации через новую систему. Если вы видите этот пост — значит, всё работает корректно. ✅", date: "2026-09-27", dateLabel: "27 сент. 2026 г.", dateLabelEn: "Sep 27, 2026", readTime: "1", readTimeEn: "1", image: "", tags: ["Tips"] },
    { id: "post-be9829a0", slug: "post-be9829a0", category: "Tips", categoryEn: "Tips", title: "Тест публикации с изображением", titleEn: "Тест публикации с изображением", excerpt: "🧪 Тест публикации с изображением Проверяем, передаётся ли изображение из MCP-коннектора Public Bot Publisher в блог ParallelLingvo вместе с текстом публикации.", excerptEn: "🧪 Тест публикации с изображением Проверяем, передаётся ли изображение из MCP-коннектора Public Bot Publisher в блог ParallelLingvo вместе с текстом публикации.", date: "2026-09-27", dateLabel: "27 сент. 2026 г.", dateLabelEn: "Sep 27, 2026", readTime: "1", readTimeEn: "1", image: "/assets/blog/post-be9829a0.png", tags: ["Tips"] },
    { id: "parallel-method", slug: "parallel-method", category: "Языки", categoryEn: "Languages", title: "Как работает метод параллельного изучения", titleEn: "How the parallel learning method works", excerpt: "Одно слово открывает дверь сразу в несколько языков — разбираем механику.", excerptEn: "One word opens the door to several languages at once — the mechanics.", date: "2026-09-11", dateLabel: "11 сент. 2026 г.", dateLabelEn: "Sep 11, 2026", readTime: "6", readTimeEn: "6", image: "", tags: ["Languages","Learning","Tips"] }
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
        img.src = a.image || '/assets/blog-placeholder.svg';
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
