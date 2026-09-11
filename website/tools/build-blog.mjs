#!/usr/bin/env node
// Builds the blog from website/content/blog/*.json into:
//   - website/blog/<slug>/index.html            (English)
//   - website/ru/blog/<slug>/index.html          (Russian, only if a "ru" locale exists in the content file)
//   - website/assets/blog.js  (ARTICLES array)
//   - website/sitemap.xml     (between the BLOG-POSTS markers)
//   - website/feed.xml        (between the ITEMS markers)
//   - website/llms.txt / llms-full.txt (between the BLOG-LIST markers)
//
// Usage: node tools/build-blog.mjs   (run from website/)
//
// To add a post: create content/blog/<slug>.json (copy an existing one as a
// starting point), fill in "en" and optionally "ru" under "locales", then
// run this script and commit the changed files.
// To add a translation to an existing post later: open its content/blog/<slug>.json
// and add the new locale under "locales", then re-run this script.

import { readFileSync, writeFileSync, readdirSync, mkdirSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url))); // website/
const CONTENT_DIR = path.join(ROOT, 'content', 'blog');
const SITE = 'https://parallellingvo.app';

const LOCALE_STRINGS = {
  en: {
    htmlLang: 'en',
    ogLocale: 'en_US',
    prefix: '',
    home: SITE + '/',
    homeLabel: 'Home',
    blogLabel: 'Blog',
    toggleThemeTitle: 'Toggle theme',
    signUp: 'Sign up',
    continueTelegram: 'Continue with Telegram',
    continueGoogle: 'Continue with Google',
    continueEmail: 'Continue with email',
    langBtn: 'EN',
    langMenu: [
      { label: 'Русский', locale: 'ru' },
      { label: 'English', locale: 'en' },
    ],
    ctaHeading: 'Ready to try it?',
    ctaText: 'Start learning several languages at once around one word — free, no limits.',
    ctaButton: 'Start for free',
    footerTagline: 'One word. Every language you speak.',
    footerSub: 'Connected vocabulary learning across 48 languages.',
    footerProductTitle: 'Product',
    footerProduct: [
      ['Try it', '#demo'], ['How it works', '#how'],
      ['Word sources', '#add-words'], ['Family accounts', '#family'],
    ],
    footerLearnTitle: 'Learn',
    footerFaq: 'FAQ',
    footerSocialTitle: 'Social',
    footerBottom: '© 2026 ParallelLingvo',
    heroAlt: 'Article hero image',
    readSuffix: 'min read',
  },
  ru: {
    htmlLang: 'ru',
    ogLocale: 'ru_RU',
    prefix: 'ru/',
    home: SITE + '/ru/',
    homeLabel: 'На главную',
    blogLabel: 'Blog',
    toggleThemeTitle: 'Переключить тему',
    signUp: 'Зарегистрироваться',
    continueTelegram: 'Через Telegram',
    continueGoogle: 'Через Google',
    continueEmail: 'Через почту',
    langBtn: 'RU',
    langMenu: [
      { label: 'Русский', locale: 'ru' },
      { label: 'English', locale: 'en' },
    ],
    ctaHeading: 'Готовы попробовать?',
    ctaText: 'Начните учить сразу несколько языков вокруг одного слова — бесплатно и без ограничений.',
    ctaButton: 'Начать бесплатно',
    footerTagline: 'Одно слово. Все языки, что вы учите.',
    footerSub: 'Связанное изучение слов на 48 языках.',
    footerProductTitle: 'Продукт',
    footerProduct: [
      ['Демо', '#demo'], ['Как работает', '#how'],
      ['Источники слов', '#add-words'], ['Семейный аккаунт', '#family'],
    ],
    footerLearnTitle: 'Материалы',
    footerFaq: 'FAQ',
    footerSocialTitle: 'Мы в соцсетях',
    footerBottom: '© 2026 ParallelLingvo',
    heroAlt: 'Главное изображение статьи',
    readSuffix: 'мин чтения',
  },
};

const SOCIAL_ICONS_HTML = `
        <a class="icon-btn" href="https://facebook.com/parallellingvo" target="_blank" rel="noopener" title="Facebook"><svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M14 8.5h2.5V5.3c-.43-.06-1.9-.18-3.2-.18-3.4 0-5 2.1-5 5.2v2.4H5.5V16h2.8v8h3.4v-8h3l.5-3.3h-3.5v-2c0-1 .3-2.2 2.3-2.2z" fill="currentColor"></path></svg></a>
        <a class="icon-btn" href="https://instagram.com/parallellingvo" target="_blank" rel="noopener" title="Instagram"><svg width="15" height="15" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="18" height="18" rx="5" stroke="currentColor" stroke-width="1.8"></rect><circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="1.8"></circle><circle cx="17.2" cy="6.8" r="1.1" fill="currentColor"></circle></svg></a>
        <a class="icon-btn" href="https://t.me/parallellingvo" target="_blank" rel="noopener" title="Telegram"><svg width="15" height="15" viewBox="0 0 240 240"><circle cx="120" cy="120" r="120" fill="#229ED9"></circle><path fill="#fff" d="M54 118l125-48c6-2 11 1 9 10l-21 100c-2 8-7 10-14 6l-38-28-18 17c-2 2-4 4-8 4l3-40 74-67c3-3-1-5-5-2l-91 57-39-12c-8-3-8-9 2-13z"></path></svg></a>`;

function signupMenuHtml(s) {
  return `
          <div id="signup-menu" class="dropdown-panel top-right" data-menu hidden>
            <a class="dropdown-item link" href="${SITE}/auth"><svg width="15" height="15" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.07 5.07 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"></path><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.99.66-2.25 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.85A11 11 0 0 0 12 23z"></path><path fill="#FBBC05" d="M5.84 14.09A6.6 6.6 0 0 1 5.5 12c0-.73.13-1.43.34-2.09V7.06H2.18A11 11 0 0 0 1 12c0 1.77.43 3.45 1.18 4.94z"></path><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1a11 11 0 0 0-9.82 6.06l3.66 2.85C6.71 7.31 9.14 5.38 12 5.38z"></path></svg>${s.continueGoogle}</a>
            <a class="dropdown-item link" href="${SITE}/auth"><svg width="15" height="15" viewBox="0 0 240 240"><circle cx="120" cy="120" r="120" fill="#229ED9"></circle><path fill="#fff" d="M54 118l125-48c6-2 11 1 9 10l-21 100c-2 8-7 10-14 6l-38-28-18 17c-2 2-4 4-8 4l3-40 74-67c3-3-1-5-5-2l-91 57-39-12c-8-3-8-9 2-13z"></path></svg>${s.continueTelegram}</a>
            <a class="dropdown-item link" href="${SITE}/auth"><svg width="15" height="15" viewBox="0 0 24 24" fill="none"><rect x="2" y="4" width="20" height="16" rx="2.5" stroke="#5D12C7" stroke-width="1.8"></rect><path d="M3 6l9 7 9-7" stroke="#5D12C7" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg>${s.continueEmail}</a>
          </div>`;
}

function esc(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function bodyHtml(body) {
  return body.map((block) => {
    if (block.type === 'h2') return `      <h2>${esc(block.text)}</h2>`;
    if (block.type === 'quote') return `      <blockquote>${esc(block.text)}</blockquote>`;
    return `      <p>${esc(block.text)}</p>`;
  }).join('\n');
}

function renderArticle(slug, date, locale, content) {
  const s = LOCALE_STRINGS[locale];
  const url = `${SITE}/${s.prefix}blog/${slug}/`;
  const enUrl = `${SITE}/blog/${slug}/`;
  const ruUrl = `${SITE}/ru/blog/${slug}/`;
  const tagsHtml = content.tags.map((t) => `      <span class="article-tag">${esc(t)}</span>`).join('\n');
  const langMenuHtml = s.langMenu.map((l) => {
    const href = l.locale === 'en' ? enUrl : ruUrl;
    return `          <a class="dropdown-item link" href="${href}">${l.label}</a>`;
  }).join('\n');
  const footerProductHtml = s.footerProduct.map(([label, anchor]) =>
    `          <a href="${s.home}${anchor}">${label}</a>`).join('\n');

  return `<!DOCTYPE html>
<html lang="${s.htmlLang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>(function(){try{var t=localStorage.getItem('pl-theme');if(t!=='dark'&&t!=='light')t=(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';document.documentElement.setAttribute('data-theme',t);}catch(e){}})();</script>
<title>${esc(content.title)} — ParallelLingvo</title>
<meta name="description" content="${esc(content.description)}">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="canonical" href="${url}">
<link rel="alternate" hreflang="en" href="${enUrl}">
<link rel="alternate" hreflang="ru" href="${ruUrl}">
<link rel="alternate" hreflang="x-default" href="${enUrl}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="ParallelLingvo">
<meta property="og:title" content="${esc(content.title)}">
<meta property="og:description" content="${esc(content.description)}">
<meta property="og:url" content="${url}">
<meta property="og:locale" content="${s.ogLocale}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${esc(content.title)}">
<meta name="twitter:description" content="${esc(content.description)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,800&family=Instrument+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/styles.css">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "${esc(content.title)}",
  "description": "${esc(content.description)}",
  "author": {"@type": "Organization", "name": "${esc(content.author)}"},
  "publisher": {"@type": "Organization", "name": "ParallelLingvo", "logo": {"@type": "ImageObject", "url": "${SITE}/assets/new-logo-full.png"}},
  "datePublished": "${date}",
  "dateModified": "${date}",
  "inLanguage": "${locale}",
  "mainEntityOfPage": {"@type": "WebPage", "@id": "${url}"},
  "keywords": "${esc(content.tags.join(', '))}"
}
</script>
</head>
<body>
<div class="pl-root">

  <header class="site-header blog-header">
    <div class="container">
      <a href="${s.home}" class="brand">
        <img class="js-logo" src="/assets/new-logo-full.png" alt="ParallelLingvo">
      </a>
      <button type="button" class="theme-btn js-theme-toggle" title="${s.toggleThemeTitle}"><span class="js-theme-icon">☾</span></button>
      <div class="social-row">${SOCIAL_ICONS_HTML}
      </div>
      <div class="lang-wrap">
        <button type="button" class="lang-btn" data-toggle="lang-menu">🌐 ${s.langBtn} <span style="font-size:9px;color:#8A7A9E;">▾</span></button>
        <div id="lang-menu" class="lang-menu-small" data-menu hidden>
${langMenuHtml}
        </div>
      </div>
      <nav class="main-nav blog-nav">
        <a href="${s.home}" style="display:flex;align-items:center;gap:6px;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path></svg>${s.homeLabel}</a>
        <a href="${SITE}/${s.prefix}blog/">${s.blogLabel}</a>
        <div class="dropdown">
          <button type="button" class="btn btn-purple" style="padding:9px 16px;font-size:13.5px;" data-toggle="signup-menu">${s.signUp} <span class="caret">▾</span></button>${signupMenuHtml(s)}
        </div>
      </nav>
    </div>
  </header>

  <article class="article-page" itemscope itemtype="https://schema.org/Article">
    <div class="article-eyebrow">${esc(content.eyebrow)}</div>
    <h1 itemprop="headline">${esc(content.title)}</h1>
    <p class="article-sub" itemprop="description">${esc(content.description)}</p>
    <div class="article-byline">
      <address itemprop="author" style="font-style:normal;display:inline;">${esc(content.author)}</address><span>·</span><time itemprop="datePublished" datetime="${date}">${esc(content.dateLabel)}</time><span>·</span><span>${content.readMinutes} ${s.readSuffix}</span>
    </div>

    <img class="article-hero" src="/assets/blog-placeholder.svg" alt="${s.heroAlt}">

    <div class="article-body">
${bodyHtml(content.body)}
    </div>

    <div class="article-tags">
${tagsHtml}
    </div>
  </article>

  <section class="article-cta-wrap">
    <div class="article-cta">
      <h3>${s.ctaHeading}</h3>
      <p>${s.ctaText}</p>
      <div class="dropdown">
        <button type="button" class="btn btn-purple" data-toggle="cta-menu">${s.ctaButton} <span class="caret">▾</span></button>
        <div id="cta-menu" class="dropdown-panel center-below" data-menu hidden>
          <a class="dropdown-item link" href="${SITE}/auth"><svg width="15" height="15" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.07 5.07 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"></path><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.99.66-2.25 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.85A11 11 0 0 0 12 23z"></path><path fill="#FBBC05" d="M5.84 14.09A6.6 6.6 0 0 1 5.5 12c0-.73.13-1.43.34-2.09V7.06H2.18A11 11 0 0 0 1 12c0 1.77.43 3.45 1.18 4.94z"></path><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1a11 11 0 0 0-9.82 6.06l3.66 2.85C6.71 7.31 9.14 5.38 12 5.38z"></path></svg>${s.continueGoogle}</a>
          <a class="dropdown-item link" href="${SITE}/auth"><svg width="15" height="15" viewBox="0 0 240 240"><circle cx="120" cy="120" r="120" fill="#229ED9"></circle><path fill="#fff" d="M54 118l125-48c6-2 11 1 9 10l-21 100c-2 8-7 10-14 6l-38-28-18 17c-2 2-4 4-8 4l3-40 74-67c3-3-1-5-5-2l-91 57-39-12c-8-3-8-9 2-13z"></path></svg>${s.continueTelegram}</a>
          <a class="dropdown-item link" href="${SITE}/auth"><svg width="15" height="15" viewBox="0 0 24 24" fill="none"><rect x="2" y="4" width="20" height="16" rx="2.5" stroke="#5D12C7" stroke-width="1.8"></rect><path d="M3 6l9 7 9-7" stroke="#5D12C7" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg>${s.continueEmail}</a>
        </div>
      </div>
    </div>
  </section>

  <footer class="site-footer">
    <div class="footer-top">
      <div class="footer-brand">
        <img class="js-footer-logo" src="/assets/logo-wordmark.png" alt="ParallelLingvo">
        <p>${s.footerTagline}</p>
        <p class="sub">${s.footerSub}</p>
      </div>
      <div class="footer-cols">
        <div class="footer-col">
          <div class="footer-col-title">${s.footerProductTitle}</div>
${footerProductHtml}
        </div>
        <div class="footer-col">
          <div class="footer-col-title">${s.footerLearnTitle}</div>
          <a href="${SITE}/${s.prefix}blog/">${s.blogLabel}</a>
          <a href="${s.home}#faq">${s.footerFaq}</a>
        </div>
        <div class="footer-col">
          <div class="footer-col-title">${s.footerSocialTitle}</div>
          <a href="https://facebook.com/parallellingvo" target="_blank" rel="noopener"><svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M14 8.5h2.5V5.3c-.43-.06-1.9-.18-3.2-.18-3.4 0-5 2.1-5 5.2v2.4H5.5V16h2.8v8h3.4v-8h3l.5-3.3h-3.5v-2c0-1 .3-2.2 2.3-2.2z" fill="currentColor"></path></svg>Facebook</a>
          <a href="https://instagram.com/parallellingvo" target="_blank" rel="noopener"><svg width="15" height="15" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="18" height="18" rx="5" stroke="currentColor" stroke-width="1.8"></rect><circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="1.8"></circle><circle cx="17.2" cy="6.8" r="1.1" fill="currentColor"></circle></svg>Instagram</a>
          <a href="https://t.me/parallellingvo" target="_blank" rel="noopener"><svg width="15" height="15" viewBox="0 0 240 240"><circle cx="120" cy="120" r="120" fill="#229ED9"></circle><path fill="#fff" d="M54 118l125-48c6-2 11 1 9 10l-21 100c-2 8-7 10-14 6l-38-28-18 17c-2 2-4 4-8 4l3-40 74-67c3-3-1-5-5-2l-91 57-39-12c-8-3-8-9 2-13z"></path></svg>Telegram</a>
        </div>
      </div>
    </div>
    <div class="footer-bottom">${s.footerBottom}</div>
  </footer>
</div>

<script src="/assets/main.js"></script>
</body>
</html>
`;
}

function loadPosts() {
  const files = readdirSync(CONTENT_DIR).filter((f) => f.endsWith('.json'));
  return files.map((f) => JSON.parse(readFileSync(path.join(CONTENT_DIR, f), 'utf8')))
    .sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));
}

function writeArticles(posts) {
  for (const post of posts) {
    for (const locale of Object.keys(post.locales)) {
      const dir = locale === 'en'
        ? path.join(ROOT, 'blog', post.slug)
        : path.join(ROOT, locale, 'blog', post.slug);
      mkdirSync(dir, { recursive: true });
      writeFileSync(path.join(dir, 'index.html'), renderArticle(post.slug, post.date, locale, post.locales[locale]));
    }
  }
}

function updateBlogJs(posts) {
  const file = path.join(ROOT, 'assets', 'blog.js');
  let src = readFileSync(file, 'utf8');
  const dateFmt = (iso, locale) => {
    const d = new Date(iso + 'T00:00:00Z');
    return d.toLocaleDateString(locale === 'ru' ? 'ru-RU' : 'en-US', { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' });
  };
  const entries = posts.map((post) => {
    const ru = post.locales.ru || post.locales.en; // fall back to English copy until a translation is loaded
    const en = post.locales.en;
    const jsStr = (v) => JSON.stringify(v);
    return `    { id: ${jsStr(post.slug)}, slug: ${jsStr(post.slug)}, category: ${jsStr(ru.eyebrow)}, categoryEn: ${jsStr(en.eyebrow)}, title: ${jsStr(ru.title)}, titleEn: ${jsStr(en.title)}, excerpt: ${jsStr(ru.description)}, excerptEn: ${jsStr(en.description)}, date: ${jsStr(post.date)}, dateLabel: ${jsStr(dateFmt(post.date, 'ru'))}, dateLabelEn: ${jsStr(dateFmt(post.date, 'en'))}, readTime: ${jsStr(String(ru.readMinutes))}, readTimeEn: ${jsStr(String(en.readMinutes))}, tags: ${jsStr(en.tags)} }`;
  });
  const block = `  var ARTICLES = [\n${entries.join(',\n')}\n  ];`;
  src = src.replace(/  var ARTICLES = \[[\s\S]*?\n  \];/, block);
  writeFileSync(file, src);
}

function updateSitemap(posts) {
  const file = path.join(ROOT, 'sitemap.xml');
  let src = readFileSync(file, 'utf8');
  const urlBlock = (loc, hreflangBase, lastmod, priority) => `  <url>
    <loc>${loc}</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>${priority}</priority>
    <xhtml:link rel="alternate" hreflang="en" href="${hreflangBase}"/>
    <xhtml:link rel="alternate" hreflang="ru" href="${hreflangBase.replace(SITE + '/', SITE + '/ru/')}"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="${hreflangBase}"/>
  </url>`;
  const blocks = posts.map((post) => {
    const enUrl = `${SITE}/blog/${post.slug}/`;
    const ruUrl = `${SITE}/ru/blog/${post.slug}/`;
    const parts = [urlBlock(enUrl, enUrl, post.date, '0.8')];
    if (post.locales.ru) parts.push(urlBlock(ruUrl, enUrl, post.date, '0.8'));
    return parts.join('\n');
  }).join('\n\n');
  src = src.replace(/<!-- BLOG-POSTS:START -->[\s\S]*?<!-- BLOG-POSTS:END -->/, `<!-- BLOG-POSTS:START -->\n${blocks}\n  <!-- BLOG-POSTS:END -->`);
  writeFileSync(file, src);
}

function rfc822(iso) {
  return new Date(iso + 'T10:00:00Z').toUTCString().replace('GMT', 'GMT');
}

function updateFeed(posts) {
  const file = path.join(ROOT, 'feed.xml');
  let src = readFileSync(file, 'utf8');
  const items = posts.map((post) => {
    const en = post.locales.en;
    const url = `${SITE}/blog/${post.slug}/`;
    return `    <item><title>${esc(en.title)}</title><link>${url}</link><guid isPermaLink="true">${url}</guid><pubDate>${rfc822(post.date)}</pubDate><description>${esc(en.description)}</description></item>`;
  }).join('\n');
  src = src.replace(/<!-- ITEMS:START -->[\s\S]*?<!-- ITEMS:END -->/, `<!-- ITEMS:START -->\n${items}\n    <!-- ITEMS:END -->`);
  src = src.replace(/<lastBuildDate>.*<\/lastBuildDate>/, `<lastBuildDate>${new Date().toUTCString()}</lastBuildDate>`);
  writeFileSync(file, src);
}

function updateLlms(posts) {
  for (const [name, numbered] of [['llms.txt', true], ['llms-full.txt', true]]) {
    const file = path.join(ROOT, name);
    let src = readFileSync(file, 'utf8');
    const lines = posts.map((post, i) => {
      const en = post.locales.en;
      return `${i + 1}. ${en.title} — ${en.description} ${SITE}/blog/${post.slug}/`;
    }).join('\n');
    src = src.replace(/<!-- BLOG-LIST:START -->[\s\S]*?<!-- BLOG-LIST:END -->/, `<!-- BLOG-LIST:START -->\n${lines}\n<!-- BLOG-LIST:END -->`);
    writeFileSync(file, src);
  }
}

const posts = loadPosts();
writeArticles(posts);
updateBlogJs(posts);
updateSitemap(posts);
updateFeed(posts);
updateLlms(posts);
console.log(`Built ${posts.length} blog post(s): ${posts.map((p) => p.slug).join(', ')}`);
