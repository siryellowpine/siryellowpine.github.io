#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, os, sys, re, html

SITE_TITLE = "Yakup Sarıçam"
EXCERPT_LEN = 90

CATEGORIES = [
    {"name": "Shipping & Maritime", "children": ["Freight Market Analysis", "Maritime News & Trends"]},
    {"name": "Books, Literature & Art", "children": ["Recommendations", "Forewords", "Reviews & Critiques"]},
    {"name": "Essays & Articles", "children": ["Personal Opinions"]},
    {"name": "Global Trends", "children": []},
]

def slugify(s: str) -> str:
    s = s.strip().lower().replace("&","and").replace(","," ")
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.replace(" ", "-")

def escape(s: str) -> str:
    return html.escape(s, quote=True)

def build_menu_html() -> str:
    def s(x): return slugify(x)
    parts = []
    for c in CATEGORIES:
        subs = ""
        if c["children"]:
            subs = "<div class='sub'>" + "".join(
                f"<a href='index.html#cat={s(c['name'])}&sub={s(ch)}'>{escape(ch)}</a>"
                for ch in c["children"]
            ) + "</div>"
        parts.append(f"<div class='cat'><span><a href='index.html#cat={s(c['name'])}'>{escape(c['name'])}</a></span>{subs}</div>")
    return "".join(parts)

def paragraphs_html(text: str) -> str:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    return "".join(f"<p>{escape(p)}</p>" for p in paras)

def build_post_html(site_title, menu_html, title, category, subcategory, date, content) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(title)} — {escape(site_title)}</title>
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../css/style.css">
  <meta name="theme-color" content="#3f342a" />
</head>
<body>
  <header>
    <div class="wrap">
      <div class="topnav">
        <div>
          <a href="../index.html">Home</a>
          <a href="../about.html">About</a>
        </div>
      </div>
      <div class="brand">
        <img class="logo" src="../favicon.svg" alt="YS monogram">
        <h1>{escape(site_title)}</h1>
      </div>
      <nav class="menu">{menu_html}</nav>
    </div>
  </header>

  <main>
    <div class="wrap">
      <article class="card">
        <div class="post-header">
          <div class="date-badge">{escape(date)}</div>
          <div class="meta">
            <a class="tag" href="../index.html#cat={slugify(category)}">{escape(category)}</a>
            <a class="tag" href="../index.html#cat={slugify(category)}&sub={slugify(subcategory)}">{escape(subcategory)}</a>
          </div>
          <h2 class="title">{escape(title)}</h2>
        </div>
        <div class="post-body">
          {paragraphs_html(content)}
        </div>
        <div class="actions"><a class="btn" href="../index.html">← Back to home</a></div>
      </article>
    </div>
  </main>

  <footer>
    <div class="wrap">© <span id="year"></span> {escape(site_title)}</div>
  </footer>
  <script>document.getElementById("year").textContent = new Date().getFullYear();</script>
</body>
</html>
"""

def build_index_scaffold(menu_html: str, site_title: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(site_title)}</title>
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="css/style.css">
  <meta name="theme-color" content="#3f342a" />
</head>
<body>
  <header>
    <div class="wrap">
      <div class="topnav">
        <div>
          <a href="index.html">Home</a>
          <a href="about.html">About</a>
        </div>
      </div>
      <div class="brand">
        <img class="logo" src="favicon.svg" alt="YS monogram">
        <h1>{escape(site_title)}</h1>
      </div>
      <nav class="menu">{menu_html}</nav>
    </div>
  </header>
  <main>
    <div class="wrap">
      <section id="list"></section>
    </div>
  </main>
  <footer>
    <div class="wrap">© <span id="year"></span> {escape(site_title)}</div>
  </footer>
  <script>
    document.getElementById("year").textContent = new Date().getFullYear();
    function parseHash(){{
      const h = location.hash.startsWith('#') ? location.hash.slice(1) : '';
      const p = new URLSearchParams(h);
      return {{cat: p.get('cat'), sub: p.get('sub')}};
    }}
    function applyFilter(){{
      const q = parseHash();
      document.querySelectorAll('#list article').forEach(a=>{{
        const okCat = !q.cat || a.dataset.cat === q.cat;
        const okSub = !q.sub || a.dataset.sub === q.sub;
        a.style.display = (okCat && okSub) ? '' : 'none';
      }});
    }}
    window.addEventListener('hashchange', applyFilter);
    applyFilter();
  </script>
</body>
</html>
"""

def build_index_card(title, category, subcategory, date, slug, content) -> str:
    preview = re.sub(r"\s+", " ", content.strip())[:EXCERPT_LEN] + "…"
    return f"""
        <article class="card" data-cat="{slugify(category)}" data-sub="{slugify(subcategory)}">
          <div class="date-badge">{escape(date)}</div>
          <div class="meta">
            <a class="tag" href="index.html#cat={slugify(category)}">{escape(category)}</a>
            <a class="tag" href="index.html#cat={slugify(category)}&sub={slugify(subcategory)}">{escape(subcategory)}</a>
          </div>
          <h2 class="title">{escape(title)}</h2>
          <p class="excerpt">{escape(preview)}</p>
          <div class="actions">
            <a class="btn" href="posts/{escape(slug)}.html">Read more</a>
          </div>
        </article>
""".rstrip()

def main_cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--category", required=True)
    ap.add_argument("--subcategory", required=True)
    ap.add_argument("--date", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--content_file")
    g.add_argument("--content_text")
    ap.add_argument("--outdir", default=".")
    args = ap.parse_args()

    if args.content_file and os.path.exists(args.content_file):
        with open(args.content_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
    elif args.content_text:
        content = args.content_text.strip()
    else:
        print("Error: Provide --content_file or --content_text", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.join(args.outdir, "posts"), exist_ok=True)
    menu_html = build_menu_html()
    slug = slugify(args.title)
    post_filename = os.path.join(args.outdir, "posts", f"{slug}.html")
    index_filename = os.path.join(args.outdir, "index.html")

    # Write/refresh index scaffold if missing
    if os.path.exists(index_filename):
        with open(index_filename, "r", encoding="utf-8") as f:
            current_index = f.read()
    else:
        current_index = ""
    if "<section id=\\"list\\"" not in current_index:
        current_index = build_index_scaffold(menu_html, SITE_TITLE)

    # Insert new card just before </section>
    card_html = build_index_card(args.title, args.category, args.subcategory, args.date, slug, content)
    updated_index = current_index.replace("</section>", card_html + "\n      </section>", 1)
    with open(index_filename, "w", encoding="utf-8") as f:
        f.write(updated_index)

    # Write post page
    post_html = build_post_html(SITE_TITLE, menu_html, args.title, args.category, args.subcategory, args.date, content)
    with open(post_filename, "w", encoding="utf-8") as f:
        f.write(post_html)

    print("Created:", post_filename)
    print("Updated:", index_filename)

if __name__ == "__main__":
    main_cli()
