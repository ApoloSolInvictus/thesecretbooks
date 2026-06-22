#!/usr/bin/env python3
"""Export the public WordPress content for The Secret Books to static HTML."""

from __future__ import annotations

import html
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


BASE_URL = "https://dev-the-secret-books.pantheonsite.io"
FALLBACK_URL = "https://live-the-secret-books.pantheonsite.io"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
ASSETS = OUT / "assets"
USER_AGENT = "TheSecretBooksStaticExporter/1.0"
PDF_OVERRIDES = {
    "jasher": "https://www.holybooks.com/wp-content/uploads/Book-of-Jasher.pdf",
}


@dataclass
class Book:
    id: int
    slug: str
    title: str
    excerpt: str
    pdf_url: str
    pdf_asset: str
    cover_url: str
    cover_asset: str
    original_url: str
    source_site: str
    pdf_note: str


def request_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=90) as response:
        return response.read()


def request_json(url: str) -> Any:
    return json.loads(request_bytes(url).decode("utf-8"))


def wp_json(path: str, base_url: str = BASE_URL) -> Any:
    return request_json(f"{base_url}/{path.lstrip('/')}")


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def escape(value: str) -> str:
    return html.escape(value or "", quote=True)


def slugify_file(name: str) -> str:
    name = unquote(name).strip()
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name or "asset"


def asset_name_for(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    return slugify_file(name)


def normalize_wp_asset_url(url: str, source_site: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    source_host = urlparse(source_site).netloc
    if "/wp-content/uploads/" in parsed.path and parsed.netloc and parsed.netloc != source_host:
        return f"{source_site.rstrip('/')}{parsed.path}"
    return url


def download_asset(url: str, subdir: str) -> str:
    if not url:
        return ""

    asset_dir = ASSETS / subdir
    asset_dir.mkdir(parents=True, exist_ok=True)
    name = asset_name_for(url)
    dest = asset_dir / name

    if not dest.exists() or dest.stat().st_size == 0:
        print(f"download {subdir}/{name}")
        try:
            dest.write_bytes(request_bytes(url))
        except Exception as exc:  # noqa: BLE001
            print(f"warning: could not download {url}: {exc}")
            return url

    return f"assets/{subdir}/{name}".replace("\\", "/")


def rel(path: str, depth: int) -> str:
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return "../" * depth + path


def extract_pdf(content: str) -> str:
    content = content.replace("\\/", "/")
    match = re.search(r'"source"\s*:\s*"([^"]+?\.pdf)"', content, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"https://[^\"'\s<>]+?\.pdf", content, re.IGNORECASE)
    return match.group(0) if match else ""


def extract_thumb(content: str) -> str:
    match = re.search(r'\bthumb="([^"]+)"', content)
    return match.group(1) if match else ""


def page_start(title: str, depth: int = 0, body_class: str = "") -> str:
    css = rel("assets/css/styles.css", depth)
    js = rel("assets/js/site.js", depth)
    icon = rel("assets/img/TSB-Logo-App-50x50.png", depth)
    nav = [
        ("Home", rel("index.html", depth)),
        ("Books", rel("books/index.html", depth)),
        ("iBook", rel("ibook/index.html", depth)),
        ("App", rel("secret-app/index.html", depth)),
    ]
    nav_html = "\n".join(f'<a href="{href}">{label}</a>' for label, href in nav)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} - The Secret Books</title>
  <meta name="description" content="The Secret Books: a static library of apocryphal and lost biblical books.">
  <link rel="icon" href="{icon}">
  <link rel="stylesheet" href="{css}">
  <script defer src="{js}"></script>
</head>
<body class="{escape(body_class)}">
  <header class="site-header">
    <a class="brand" href="{rel('index.html', depth)}">
      <img src="{rel('assets/img/TSB-Logo-App-250x250.png', depth)}" alt="">
      <span>The Secret Books</span>
    </a>
    <nav aria-label="Primary navigation">
      {nav_html}
    </nav>
  </header>
"""


def page_end(depth: int = 0) -> str:
    return f"""
  <footer class="site-footer">
    <p>The Secret Books static edition. Source content exported from WordPress on Pantheon.</p>
    <a href="{rel('data/inventory.json', depth)}">Inventory</a>
  </footer>
</body>
</html>
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def book_card(book: Book, depth: int = 0) -> str:
    cover = rel(book.cover_asset, depth)
    href = rel(f"{book.slug}/index.html", depth)
    return f"""
      <article class="book-card" data-title="{escape(book.title.lower())}">
        <a href="{href}">
          <img src="{cover}" alt="">
          <span>{escape(book.title)}</span>
        </a>
      </article>
"""


def render_home(books: list[Book], assets: dict[str, str]) -> str:
    featured = books[-8:][::-1]
    cards = "".join(book_card(book, 0) for book in featured)
    hero_bg = rel(assets["hero_bg"], 0)
    logo = rel(assets["logo"], 0)
    book = rel(assets["book"], 0)
    read_bg = rel(assets["read_bg"], 0)
    character_bg = rel(assets["character_bg"], 0)
    character_img = rel(assets["character_img"], 0)
    return page_start("Discover", 0, "home") + f"""
  <main>
    <section class="hero" style="--hero-image: url('{hero_bg}')">
      <div class="hero-mask"></div>
      <div class="hero-copy">
        <img class="hero-logo" src="{logo}" alt="The Secret Books">
        <h1>The Secret Books</h1>
        <p>Ancient writings, apocrypha, visions, gospels, epistles, and hidden histories gathered into one quiet library.</p>
        <div class="hero-actions">
          <a class="button primary" href="books/index.html">Enter the Library</a>
          <a class="button" href="ibook/index.html">Open iBook</a>
        </div>
      </div>
      <img class="hero-book" src="{book}" alt="">
    </section>

    <section class="book-read" style="--read-image: url('{read_bg}')">
      <div class="book-read-inner">
        <p class="eyebrow">Discover</p>
        <h2>Lost books gathered in one place</h2>
        <p>This static edition keeps the Pantheon imagery and makes the library portable for GitHub Pages: no WordPress server needed, no checkout required to read.</p>
      </div>
    </section>

    <section class="characters-information" style="--character-image: url('{character_bg}')">
      <h2>Meet the Books</h2>
      <div class="character-slide">
        <img src="{character_img}" alt="">
        <div>
          <p class="eyebrow">Prologue</p>
          <h3>Prophets, visions, epistles and hidden histories</h3>
          <p>The collection brings the public PDFs into simple HTML pages with direct readers and downloads.</p>
        </div>
      </div>
    </section>

    <section class="author-information">
      <div class="author-photo" style="--author-image: url('{book}')"></div>
      <div class="author-bio">
        <p class="eyebrow">The Secret Books</p>
        <h2>The archive is ready for GitHub.</h2>
        <p>Every public book entry from Pantheon is exported with its cover and PDF. The inventory file records which source each book came from.</p>
      </div>
    </section>

    <section class="section band">
      <div class="section-heading">
        <p class="eyebrow">Library</p>
        <h2>{len(books)} public books gathered</h2>
      </div>
      <div class="book-grid compact">
        {cards}
      </div>
      <div class="centered">
        <a class="button primary" href="books/index.html">View All Books</a>
      </div>
    </section>
  </main>
""" + page_end(0)


def render_books_index(books: list[Book]) -> str:
    cards = "".join(book_card(book, 1) for book in books)
    return page_start("Books", 1, "library") + f"""
  <main>
    <section class="page-hero narrow">
      <p class="eyebrow">Books</p>
      <h1>The Library</h1>
      <p>{len(books)} public WordPress entries exported as static book pages with local PDF readers.</p>
      <label class="search-label">
        <span>Search</span>
        <input type="search" data-book-search placeholder="Search books">
      </label>
    </section>
    <section class="section">
      <div class="book-grid" data-book-grid>
        {cards}
      </div>
    </section>
  </main>
""" + page_end(1)


def render_book(book: Book, previous_book: Book | None, next_book: Book | None) -> str:
    cover = rel(book.cover_asset, 1)
    pdf = rel(book.pdf_asset, 1)
    prev_link = (
        f'<a class="button" href="../{previous_book.slug}/index.html">Previous</a>'
        if previous_book
        else ""
    )
    next_link = (
        f'<a class="button" href="../{next_book.slug}/index.html">Next</a>'
        if next_book
        else ""
    )
    return page_start(book.title, 1, "book-page") + f"""
  <main>
    <article class="book-layout">
      <aside class="book-aside">
        <img class="book-cover" src="{cover}" alt="">
        <a class="button primary full" href="{pdf}" download>Download PDF</a>
        <a class="button full" href="{escape(book.original_url)}">Original WordPress Page</a>
      </aside>
      <section class="book-reader">
        <p class="eyebrow">The Secret Books</p>
        <h1>{escape(book.title)}</h1>
        <p>{escape(book.excerpt or "Read the preserved PDF edition in the static library.")}</p>
        <div class="reader-actions">
          {prev_link}
          <a class="button" href="../books/index.html">All Books</a>
          {next_link}
        </div>
        <iframe class="pdf-frame" title="{escape(book.title)} PDF" src="{pdf}"></iframe>
      </section>
    </article>
  </main>
""" + page_end(1)


def render_ibook(assets: dict[str, str]) -> str:
    pdf = rel(assets["ibook_pdf"], 1)
    image = rel(assets["ibook_img"], 1)
    return page_start("iBook", 1, "product-page") + f"""
  <main>
    <section class="product-layout">
      <div class="product-copy">
        <p class="eyebrow">iBook</p>
        <h1>The Secret iBook</h1>
        <p>A visual companion edition for entering the ancient stories with a cinematic sense of place and time.</p>
        <a class="button primary" href="{pdf}" download>Download iBook PDF</a>
      </div>
      <img class="product-image" src="{image}" alt="">
    </section>
    <section class="pdf-panel">
      <iframe class="pdf-frame" title="The Secret iBook PDF" src="{pdf}"></iframe>
    </section>
  </main>
""" + page_end(1)


def render_app(assets: dict[str, str], audio_asset: str) -> str:
    app_img = rel(assets["app_img"], 1)
    audio = rel(audio_asset, 1)
    return page_start("Secret App", 1, "product-page") + f"""
  <main>
    <section class="product-layout">
      <div class="product-copy">
        <p class="eyebrow">App</p>
        <h1>Secret App</h1>
        <p>The mobile companion for The Secret Books, gathered here with the public audiobook asset from WordPress.</p>
        <div class="hero-actions">
          <a class="button primary" href="../books/index.html">Browse Books</a>
          <a class="button" href="{audio}" download>Download Audio</a>
        </div>
      </div>
      <img class="product-image phone" src="{app_img}" alt="">
    </section>
    <section class="audio-panel">
      <h2>Audiobook Asset</h2>
      <audio controls src="{audio}"></audio>
    </section>
  </main>
""" + page_end(1)


def render_placeholder(title: str, message: str, depth: int = 1) -> str:
    return page_start(title, depth, "status-page") + f"""
  <main>
    <section class="page-hero narrow">
      <p class="eyebrow">Static edition</p>
      <h1>{escape(title)}</h1>
      <p>{escape(message)}</p>
      <a class="button primary" href="{rel('books/index.html', depth)}">Return to Books</a>
    </section>
  </main>
""" + page_end(depth)


def fetch_all(endpoint: str, base_url: str = BASE_URL, per_page: int = 100) -> list[Any]:
    first_url = f"{base_url}/{endpoint.lstrip('/')}?per_page={per_page}"
    if "?" in endpoint:
        first_url = f"{base_url}/{endpoint.lstrip('/')}&per_page={per_page}"
    req = Request(first_url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=90) as response:
        total_pages = int(response.headers.get("X-WP-TotalPages", "1") or "1")

    sep = "&" if "?" in endpoint else "?"
    items: list[Any] = []
    for page in range(1, total_pages + 1):
        items.extend(wp_json(f"{endpoint}{sep}per_page={per_page}&page={page}", base_url))
    return items


def collect_books() -> list[Book]:
    fields = "_fields=id,slug,link,title,content,excerpt,featured_media&orderby=date&order=asc"
    primary_posts = fetch_all(f"wp-json/wp/v2/posts?{fields}", BASE_URL)
    fallback_posts = fetch_all(f"wp-json/wp/v2/posts?{fields}", FALLBACK_URL)
    posts_by_slug: dict[str, tuple[dict[str, Any], str]] = {
        post["slug"]: (post, BASE_URL) for post in primary_posts
    }
    for post in fallback_posts:
        posts_by_slug.setdefault(post["slug"], (post, FALLBACK_URL))

    primary_media = fetch_all(
        "wp-json/wp/v2/media?_fields=id,source_url,media_type,mime_type,title",
        BASE_URL,
    )
    fallback_media = fetch_all(
        "wp-json/wp/v2/media?_fields=id,source_url,media_type,mime_type,title",
        FALLBACK_URL,
    )
    media_by_source = {
        BASE_URL: {item["id"]: item for item in primary_media},
        FALLBACK_URL: {item["id"]: item for item in fallback_media},
    }

    books: list[Book] = []
    ordered_posts = sorted(posts_by_slug.values(), key=lambda item: item[0]["id"])
    for post, source_site in ordered_posts:
        content = post["content"]["rendered"]
        title = clean_text(post["title"]["rendered"])
        pdf_note = ""
        pdf_url = normalize_wp_asset_url(extract_pdf(content), source_site)
        if post["slug"] in PDF_OVERRIDES:
            pdf_url = PDF_OVERRIDES[post["slug"]]
            pdf_note = "Pantheon public post pointed to Baruch.pdf; exported with a public Book of Jasher PDF override."
        thumb_url = normalize_wp_asset_url(extract_thumb(content), source_site)
        featured = media_by_source[source_site].get(post.get("featured_media"))
        cover_url = normalize_wp_asset_url((featured or {}).get("source_url") or thumb_url, source_site)
        excerpt = clean_text(post.get("excerpt", {}).get("rendered", ""))

        books.append(
            Book(
                id=post["id"],
                slug=post["slug"],
                title=title,
                excerpt=excerpt,
                pdf_url=pdf_url,
                pdf_asset=download_asset(pdf_url, "pdfs"),
                cover_url=cover_url,
                cover_asset=download_asset(cover_url, "img/covers"),
                original_url=post["link"],
                source_site=source_site,
                pdf_note=pdf_note,
            )
        )

    return books


def collect_site_assets() -> tuple[dict[str, str], str]:
    urls = {
        "logo": f"{BASE_URL}/wp-content/uploads/2024/05/TSB-Logo.png",
        "app_icon": f"{BASE_URL}/wp-content/uploads/2024/05/TSB-Logo-App-250x250.png",
        "app_icon_small": f"{BASE_URL}/wp-content/uploads/2024/05/TSB-Logo-App-50x50.png",
        "hero_bg": f"{BASE_URL}/wp-content/uploads/2024/05/TDsekcUuGseauE7C6v5g-1-bfdnu.jpg",
        "read_bg": f"{BASE_URL}/wp-content/uploads/2024/05/ZrO7CPvnjYlVuk5Tb1OW-1-erpxv.jpg",
        "character_bg": f"{BASE_URL}/wp-content/uploads/2024/05/ztg8E5WLXIyupqfEpg12-1-g8k4n.jpg",
        "character_img": f"{BASE_URL}/wp-content/uploads/2024/05/rT5VkYTgYeoI8LuRowux-1-ps36q-250x250.jpg",
        "book": f"{BASE_URL}/wp-content/uploads/2024/05/book23.png",
        "ibook_img": f"{BASE_URL}/wp-content/uploads/2024/05/ibook2.png",
        "app_img": f"{BASE_URL}/wp-content/uploads/2024/05/App1.png",
        "ibook_pdf": f"{BASE_URL}/wp-content/uploads/edd/2024/05/The-Secret-Books.pdf",
    }
    assets = {key: download_asset(url, "img" if not url.endswith(".pdf") else "pdfs") for key, url in urls.items()}
    audio_url = f"{BASE_URL}/wp-content/uploads/edd/2024/06/FREE-music-Symphony-of-Specters-Intense-Cinematic-Trailer.mp3"
    audio_asset = download_asset(audio_url, "audio")
    return assets, audio_asset


def write_static_assets() -> None:
    write(
        ASSETS / "css" / "styles.css",
        """*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#d1b7e2;color:#130c0c;font-family:Arial,Helvetica,sans-serif;line-height:1.55;border:3px solid #1e73be}a{color:inherit;text-decoration:none}img{max-width:100%;display:block}.site-header{position:sticky;top:0;z-index:20;display:flex;align-items:center;justify-content:space-between;gap:24px;margin:1em;padding:12px clamp(18px,4vw,54px);background:#980000;border:3px solid #ff0000;box-shadow:5px 5px 5px 1px #ddd}.brand{display:flex;align-items:center;gap:10px;color:#fdfdfd;font-weight:800;letter-spacing:.08em;text-shadow:1px 1px 4px #000;text-transform:uppercase}.brand img{width:42px;height:42px;filter:grayscale(50%)}.site-header nav{display:flex;flex-wrap:wrap;gap:0;background:#e06666}.site-header nav a{padding:10px 14px;color:#fff;font-weight:700}.site-header nav a:hover{background:#bf9456;color:#111}.hero{position:relative;min-height:72vh;display:grid;grid-template-columns:minmax(0,1fr) minmax(240px,460px);align-items:center;gap:42px;padding:clamp(36px,6vw,82px) clamp(18px,6vw,86px);background:var(--hero-image) center/cover no-repeat;overflow:hidden}.hero-mask{position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.78),rgba(0,0,0,.28));z-index:0}.hero-copy,.hero-book{position:relative;z-index:1}.hero-logo{width:min(300px,60vw);margin-bottom:12px}.hero h1,.page-hero h1,.book-reader h1,.product-copy h1{margin:0;color:#fff;font-family:Montserrat,Arial Black,Arial,sans-serif;font-size:clamp(2.35rem,6vw,5.6rem);font-style:italic;line-height:.95;text-shadow:2px 2px 6px #000}.hero p,.page-hero p,.book-reader p,.product-copy p{max-width:720px;color:#f1c232;font-size:clamp(1rem,1.5vw,1.18rem);line-height:30px}.hero-book{max-height:58vh;justify-self:center;filter:drop-shadow(0 34px 34px rgba(0,0,0,.55))}.hero-actions,.reader-actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:22px}.button{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:10px 16px;border:1px solid #bf9456;border-radius:6px;background:#111;color:#fff;font-weight:750}.button:hover{background:#e06666;color:#111}.button.primary{background:#bf9456;color:#15120c;border-color:#bf9456}.button.full{width:100%;margin-top:10px}.book-read{padding:clamp(50px,7vw,110px) clamp(18px,8vw,100px);background:linear-gradient(90deg,rgba(0,0,0,.72),rgba(0,0,0,.38)),var(--read-image) center/cover fixed no-repeat}.book-read-inner{max-width:760px;color:#fff}.book-read h2,.characters-information h2,.author-bio h2{margin:0 0 12px;font-family:Montserrat,Arial Black,Arial,sans-serif;font-size:clamp(2rem,4.5vw,4.2rem);font-style:italic;line-height:1;color:#eeee22;text-shadow:2px 2px 4px #000}.book-read p,.characters-information p,.author-bio p{font-size:17px;line-height:30px}.characters-information{padding:clamp(42px,6vw,84px) clamp(18px,7vw,92px);background:linear-gradient(rgba(147,196,125,.9),rgba(147,196,125,.9)),var(--character-image) center/cover no-repeat}.character-slide{display:grid;grid-template-columns:250px minmax(0,680px);gap:28px;align-items:center;margin-top:24px}.character-slide img{width:250px;height:250px;object-fit:cover;border:6px solid #f1c232}.character-slide h3{margin:0;color:#741b47;font-size:clamp(1.4rem,3vw,2.4rem)}.author-information{display:grid;grid-template-columns:minmax(220px,42%) minmax(0,1fr);min-height:420px;background:#a4c2f4}.author-photo{min-height:420px;background:var(--author-image) center/contain no-repeat #111}.author-bio{padding:clamp(34px,6vw,84px);align-self:center}.section{padding:clamp(34px,5vw,72px) clamp(18px,6vw,86px)}.band{background:#93c47d}.section-heading{display:flex;align-items:end;justify-content:space-between;gap:24px;margin-bottom:24px}.section-heading h2{margin:0;font-family:Montserrat,Arial Black,Arial,sans-serif;font-size:clamp(1.8rem,4vw,3.4rem);font-style:italic;color:#000}.eyebrow{margin:0 0 8px;color:#741b47;font-size:.78rem;font-weight:850;letter-spacing:.16em;text-transform:uppercase}.book-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(176px,1fr));gap:18px}.book-grid.compact{grid-template-columns:repeat(auto-fit,minmax(154px,1fr))}.book-card{border:1px solid rgba(0,0,0,.18);border-radius:8px;background:rgba(255,255,255,.55);overflow:hidden;transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease}.book-card:hover{transform:translateY(-3px);border-color:#980000;box-shadow:0 12px 22px rgba(0,0,0,.22)}.book-card a{display:grid;grid-template-rows:1fr auto;height:100%}.book-card img{width:100%;aspect-ratio:1/1;object-fit:cover;background:#17150f}.book-card span{min-height:66px;padding:12px;color:#000;font-weight:760}.centered{text-align:center;margin-top:28px}.page-hero{padding:clamp(34px,6vw,82px) clamp(18px,6vw,86px);background:#a4c2f4;border-bottom:3px solid #1e73be}.page-hero.narrow{min-height:unset}.page-hero p,.book-reader p,.product-copy p{color:#000}.search-label{display:grid;gap:6px;max-width:520px;margin-top:24px}.search-label span{color:#741b47;font-weight:760}.search-label input{width:100%;min-height:48px;border:1px solid #980000;border-radius:6px;background:#fff;color:#17150f;padding:0 14px;font:inherit}.book-layout{display:grid;grid-template-columns:minmax(220px,340px) minmax(0,1fr);gap:34px;padding:clamp(26px,5vw,62px) clamp(18px,5vw,68px);background:#93c47d}.book-aside{position:sticky;top:110px;align-self:start}.book-cover{width:100%;border-radius:8px;border:3px solid #bf9456;background:#17150f}.book-reader{min-width:0}.book-reader h1,.product-copy h1{color:#111;text-shadow:none}.pdf-frame{width:100%;height:min(78vh,920px);margin-top:24px;border:3px solid #bf9456;border-radius:8px;background:#fff}.product-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(230px,440px);align-items:center;gap:42px;padding:clamp(34px,6vw,84px) clamp(18px,6vw,86px);background:#a4c2f4}.product-image{justify-self:center;max-height:620px;filter:drop-shadow(0 28px 30px rgba(0,0,0,.46))}.product-image.phone{max-height:520px}.pdf-panel,.audio-panel{padding:0 clamp(18px,6vw,86px) clamp(34px,6vw,72px);background:#a4c2f4}.audio-panel audio{width:100%;max-width:760px}.site-footer{display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;padding:24px clamp(18px,4vw,54px);color:#000;background:#ededed}.site-footer p{margin:0}.hidden{display:none!important}@media (max-width:760px){.site-header{align-items:flex-start;flex-direction:column}.hero,.book-layout,.product-layout,.author-information,.character-slide{grid-template-columns:1fr}.hero{min-height:58vh}.hero-book{max-height:360px}.section-heading{display:block}.book-aside{position:static}.pdf-frame{height:68vh}.book-grid{grid-template-columns:repeat(auto-fill,minmax(136px,1fr))}.book-card span{min-height:78px}.author-photo{min-height:300px}}""",
    )
    write(
        ASSETS / "js" / "site.js",
        """document.addEventListener("DOMContentLoaded",()=>{const input=document.querySelector("[data-book-search]");const grid=document.querySelector("[data-book-grid]");if(!input||!grid)return;const cards=[...grid.querySelectorAll(".book-card")];input.addEventListener("input",()=>{const q=input.value.trim().toLowerCase();cards.forEach(card=>{card.classList.toggle("hidden",q&&!card.dataset.title.includes(q));});});});""",
    )


def main() -> None:
    if OUT.exists():
        for item in OUT.iterdir():
            if item.name == "assets":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    write_static_assets()
    assets, audio_asset = collect_site_assets()
    books = collect_books()

    write(OUT / "index.html", render_home(books, assets))
    write(OUT / "books" / "index.html", render_books_index(books))
    write(OUT / "ibook" / "index.html", render_ibook(assets))
    write(OUT / "secret-app" / "index.html", render_app(assets, audio_asset))
    write(
        OUT / "login" / "index.html",
        render_placeholder("Login", "Account login is a WordPress/BuddyPress function and is not part of this static GitHub Pages edition."),
    )
    write(
        OUT / "checkout" / "index.html",
        render_placeholder("Checkout", "Checkout is powered by Easy Digital Downloads on WordPress and is not part of this static GitHub Pages edition."),
    )
    write(OUT / "404.html", render_placeholder("Page Not Found", "The page was not included in the static export.", 0))

    for index, book in enumerate(books):
        previous_book = books[index - 1] if index > 0 else None
        next_book = books[index + 1] if index + 1 < len(books) else None
        write(OUT / book.slug / "index.html", render_book(book, previous_book, next_book))

    inventory = {
        "source": BASE_URL,
        "fallback_source": FALLBACK_URL,
        "book_count": len(books),
        "books": [book.__dict__ for book in books],
        "notes": [
            "Pantheon Git clone requires a registered SSH public key.",
            "The dev WordPress REST API reported 46 public posts/books at export time.",
            "The static export includes any additional public books found on the live environment that are not present on dev.",
            "The Jasher post on Pantheon points to Baruch.pdf, so Jasher is exported with a public PDF override.",
            "Dynamic WordPress features such as login, checkout, BuddyPress, and EDD cart are represented as static placeholder pages.",
        ],
    }
    write(OUT / "data" / "inventory.json", json.dumps(inventory, indent=2, ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
