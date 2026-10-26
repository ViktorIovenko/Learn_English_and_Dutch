/* ParallelLingvo — blog index search / sort / tag filter (vanilla JS) */
(function () {
  'use strict';

  var root = document.getElementById('blog-index');
  if (!root) return;

  var LANG = (document.documentElement.lang === 'ru') ? 'ru' : 'en';
  var isRu = LANG === 'ru';
  var langPrefix = isRu ? 'ru/' : '';

  var ARTICLES = [
    { id: "why-we-forget-new-words-and-how-to-remember-them-f50e6882", slug: "why-we-forget-new-words-and-how-to-remember-them-f50e6882", category: "Vocabulary", categoryEn: "Vocabulary", title: "Why We Forget New Words — And How to Remember Them", titleEn: "Why We Forget New Words — And How to Remember Them", excerpt: "Why do familiar words disappear from memory when you need them most? Discover practical vocabulary learning techniques and how ParallelLingvo helps you review difficult words, practice pronunciation, and organize vocabulary across multiple languages.", excerptEn: "Why do familiar words disappear from memory when you need them most? Discover practical vocabulary learning techniques and how ParallelLingvo helps you review difficult words, practice pronunciation, and organize vocabulary across multiple languages.", date: "2026-10-17", dateLabel: "17 окт. 2026 г.", dateLabelEn: "Oct 17, 2026", readTime: "3", readTimeEn: "3", image: "/assets/blog/why-we-forget-new-words-and-how-to-remember-them-f50e6882-5a104f84f6cf1536.png", tags: ["Vocabulary"], url: "https://parallellingvo.app/blog/why-we-forget-new-words-and-how-to-remember-them-f50e6882/", urlRu: "https://parallellingvo.app/blog/why-we-forget-new-words-and-how-to-remember-them-f50e6882/" },
    { id: "why-do-we-keep-forgetting-the-same-words-when-learning-langu-960efac8", slug: "why-do-we-keep-forgetting-the-same-words-when-learning-langu-960efac8", category: "Vocabulary", categoryEn: "Vocabulary", title: "Why Do We Keep Forgetting the Same Words When Learning Languages?", titleEn: "Why Do We Keep Forgetting the Same Words When Learning Languages?", excerpt: "Why do we keep forgetting foreign words? Discover practical ways to improve vocabulary retention, review difficult words, and learn multiple languages more effectively.", excerptEn: "Why do we keep forgetting foreign words? Discover practical ways to improve vocabulary retention, review difficult words, and learn multiple languages more effectively.", date: "2026-10-14", dateLabel: "14 окт. 2026 г.", dateLabelEn: "Oct 14, 2026", readTime: "3", readTimeEn: "3", image: "/assets/blog/why-do-we-keep-forgetting-the-same-words-when-learning-langu-960efac8-3db209b7ef9f96a5.png", tags: ["Vocabulary"], url: "https://parallellingvo.app/blog/why-do-we-keep-forgetting-the-same-words-when-learning-langu-960efac8/", urlRu: "https://parallellingvo.app/blog/why-do-we-keep-forgetting-the-same-words-when-learning-langu-960efac8/" },
    { id: "why-learning-words-in-context-is-better-than-memorizing-tran-3686ffa1", slug: "why-learning-words-in-context-is-better-than-memorizing-tran-3686ffa1", category: "Vocabulary", categoryEn: "Vocabulary", title: "Why Learning Words in Context Is Better Than Memorizing Translations", titleEn: "Why Learning Words in Context Is Better Than Memorizing Translations", excerpt: "Memorizing translations is only the beginning. Learn how studying words in context improves understanding, strengthens memory, and builds real communication skills.", excerptEn: "Memorizing translations is only the beginning. Learn how studying words in context improves understanding, strengthens memory, and builds real communication skills.", date: "2026-10-09", dateLabel: "9 окт. 2026 г.", dateLabelEn: "Oct 9, 2026", readTime: "3", readTimeEn: "3", image: "/assets/blog/why-learning-words-in-context-is-better-than-memorizing-tran-3686ffa1-f36381fb982a8f5d.png", tags: ["Vocabulary"], url: "https://parallellingvo.app/blog/why-learning-words-in-context-is-better-than-memorizing-tran-3686ffa1/", urlRu: "https://parallellingvo.app/blog/why-learning-words-in-context-is-better-than-memorizing-tran-3686ffa1/" },
    { id: "one-word-multiple-languages-a-better-way-to-build-multilingu-932b4aad", slug: "one-word-multiple-languages-a-better-way-to-build-multilingu-932b4aad", category: "Vocabulary", categoryEn: "Vocabulary", title: "One Word, Multiple Languages: A Better Way to Build Multilingual Vocabulary", titleEn: "One Word, Multiple Languages: A Better Way to Build Multilingual Vocabulary", excerpt: "One concept, multiple languages. Discover how ParallelLingvo connects translations, simplifies vocabulary organization, and makes multilingual learning more efficient.", excerptEn: "One concept, multiple languages. Discover how ParallelLingvo connects translations, simplifies vocabulary organization, and makes multilingual learning more efficient.", date: "2026-10-05", dateLabel: "5 окт. 2026 г.", dateLabelEn: "Oct 5, 2026", readTime: "3", readTimeEn: "3", image: "/assets/blog/one-word-multiple-languages-a-better-way-to-build-multilingu-932b4aad.png", tags: ["Vocabulary"], url: "https://parallellingvo.app/blog/one-word-multiple-languages-a-better-way-to-build-multilingu-932b4aad/", urlRu: "https://parallellingvo.app/blog/one-word-multiple-languages-a-better-way-to-build-multilingu-932b4aad/" },
    { id: "how-to-learn-multiple-languages-at-the-same-time-without-mix-e496c345", slug: "how-to-learn-multiple-languages-at-the-same-time-without-mix-e496c345", category: "Tips", categoryEn: "Tips", title: "How to Learn Multiple Languages at the Same Time Without Mixing Them Up", titleEn: "How to Learn Multiple Languages at the Same Time Without Mixing Them Up", excerpt: "Can you learn several languages without mixing them up? Explore practical strategies for organizing vocabulary, comparing languages, and building lasting knowledge.", excerptEn: "Can you learn several languages without mixing them up? Explore practical strategies for organizing vocabulary, comparing languages, and building lasting knowledge.", date: "2026-09-28", dateLabel: "28 сент. 2026 г.", dateLabelEn: "Sep 28, 2026", readTime: "5", readTimeEn: "5", image: "/assets/blog/how-to-learn-multiple-languages-at-the-same-time-without-mix-e496c345.png", tags: ["Tips"], url: "https://parallellingvo.app/blog/how-to-learn-multiple-languages-at-the-same-time-without-mix-e496c345/", urlRu: "https://parallellingvo.app/blog/how-to-learn-multiple-languages-at-the-same-time-without-mix-e496c345/" },
    { id: "parallel-method", slug: "parallel-method", category: "Языки", categoryEn: "Languages", title: "Как работает метод параллельного изучения", titleEn: "How the parallel learning method works", excerpt: "Одно слово открывает дверь сразу в несколько языков — разбираем механику.", excerptEn: "One word opens the door to several languages at once — the mechanics.", date: "2026-09-11", dateLabel: "11 сент. 2026 г.", dateLabelEn: "Sep 11, 2026", readTime: "6", readTimeEn: "6", image: "/assets/blog/parallel-method-70976c2bc84f5e43.png", tags: ["Languages","Learning","Tips"], url: "https://parallellingvo.app/blog/parallel-method/", urlRu: "https://parallellingvo.app/ru/blog/parallel-method/" }
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
        // The builder resolves untranslated posts to the original's page.
        var url = (isRu ? a.urlRu : a.url) || ('https://parallellingvo.app/' + langPrefix + 'blog/' + a.slug + '/');
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
