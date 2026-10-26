"""SEO / indexing regression check for parallellingvo.app.

    python website/tools/seo_check.py                       # production
    python website/tools/seo_check.py --base http://localhost:8080

Checks (exit code 1 on any failure):
* robots.txt: public site allowed; private paths (/admin/, /api/, /auth) disallowed;
  never "Disallow: /" for everyone; Sitemap line present.
* sitemap.xml: 200; contains home, blog, every published post linked from /blog/;
  only canonical 200 pages of this host; nothing private.
* every sitemap URL: 200 without redirect, no noindex (meta or X-Robots-Tag),
  self canonical, <title>, meta description, <h1> in the server HTML.
* legacy URLs of earlier site versions: one 301 hop to a 200 page.
* /admin/: not in sitemap, noindex.
Standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlsplit

UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html) seo_check"
PRIVATE_PREFIXES = ("/admin", "/api/", "/auth", "/app", "/settings", "/upload", "/parent", "/family", "/learn")
LEGACY = ["/de/", "/es/", "/fr/", "/it/", "/ja/", "/nl/", "/pl/", "/pt/", "/zh/", "/nl/blog/",
          "/blog/how-to-learn-vocabulary-in-three-languages/", "/blog/organize-multilingual-vocabulary/",
          "/blog/telegram-mini-app-language-learning/", "/ru/blog/organize-multilingual-vocabulary/",
          "/index.md", "/blog/index.md", "/learning-languages.md"]

failures: list[str] = []


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def fetch(url: str) -> tuple[int, dict[str, str], str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with OPENER.open(req, timeout=20) as resp:
            return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}, exc.read().decode("utf-8", "replace")


def check(ok: bool, message: str) -> None:
    print(("  ok   " if ok else "  FAIL ") + message)
    if not ok:
        failures.append(message)


def meta(html: str, name: str) -> str:
    m = re.search(r'<meta\s+name="%s"\s+content="([^"]*)"' % name, html, re.I)
    return m.group(1) if m else ""


def canonical(html: str) -> str:
    m = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', html, re.I)
    return m.group(1) if m else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="https://parallellingvo.app")
    args = parser.parse_args()
    base = args.base.rstrip("/")
    canon_base = "https://parallellingvo.app"

    print("robots.txt")
    status, _, robots = fetch(base + "/robots.txt")
    check(status == 200, f"robots.txt HTTP {status}")
    lines = [l.split("#")[0].strip() for l in robots.splitlines()]
    disallows = [l.split(":", 1)[1].strip() for l in lines if l.lower().startswith("disallow:")]
    check("/" not in disallows, "no 'Disallow: /' (whole site)")
    for path in ("/admin/", "/api/", "/auth"):
        check(any(path.startswith(d.rstrip("$")) or d.rstrip("$") == path.rstrip("/") for d in disallows),
              f"robots disallows {path}")
    check(any(l.lower().startswith("sitemap:") for l in lines), "robots has Sitemap line")

    print("sitemap.xml")
    status, _, sitemap = fetch(base + "/sitemap.xml")
    check(status == 200, f"sitemap.xml HTTP {status}")
    locs = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    paths = [urlsplit(u).path for u in locs]
    check(all(u.startswith(canon_base + "/") for u in locs), "all sitemap URLs are on https://parallellingvo.app")
    for required in ("/", "/ru/", "/blog/", "/ru/blog/"):
        check(required in paths, f"sitemap contains {required}")
    check(not [p for p in paths if p.startswith(PRIVATE_PREFIXES)], "sitemap has no private/technical URLs")
    check(len(paths) == len(set(paths)), "sitemap has no duplicates")

    _, _, blog = fetch(base + "/blog/")
    posts = sorted(set(re.findall(r'href="(?:https://parallellingvo\.app)?(/blog/[a-z0-9-]+/)"', blog)))
    check(bool(posts), f"blog index links {len(posts)} posts")
    for post in posts:
        check(post in paths, f"published post in sitemap: {post}")

    print("sitemap pages")
    for url in locs:
        path = urlsplit(url).path
        status, headers, html = fetch(base + path)
        robots_meta = meta(html, "robots").lower()
        problems = []
        if status != 200:
            problems.append(f"HTTP {status}")
        if "noindex" in robots_meta or "noindex" in headers.get("x-robots-tag", "").lower():
            problems.append("noindex")
        if canonical(html) != url:
            problems.append(f"canonical={canonical(html) or '-'}")
        if not re.search(r"<title>[^<]+</title>", html):
            problems.append("no title")
        if not meta(html, "description"):
            problems.append("no description")
        if "<h1" not in html:
            problems.append("no h1")
        check(not problems, f"{path} " + (", ".join(problems) if problems else "200 index canonical title desc h1"))

    print("legacy URLs")
    for path in LEGACY:
        status, headers, _ = fetch(base + path)
        target = urljoin(base + path, headers.get("location", ""))
        final = fetch(target)[0] if status in (301, 308) else 0
        check(status in (301, 308) and final == 200, f"{path} -> {status} {urlsplit(target).path} ({final})")

    print("admin")
    status, headers, html = fetch(base + "/admin/")
    check("/admin/" not in paths, "/admin/ not in sitemap")
    check("noindex" in (headers.get("x-robots-tag", "") + meta(html, "robots")).lower(), f"/admin/ is noindex (HTTP {status})")

    print(f"\n{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
