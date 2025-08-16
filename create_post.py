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
          <a href="/">Home</a>
          <a href="/about.html">About</a>
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
            {tags_html}
          </div>
          <h2 class="title">{escape(title)}</h2>
        </div>
        <div class="post-body">
          {paragraphs_html(content)}
        </div>
        <div class="actions"><a class="btn" href="/">← Back to home</a></div>
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
    # Çoklu kategori filtresi (virgülle ayrılmış data-cat/data-sub destekli)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(site_title)}</title>
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="css/style.css">
  <meta name="theme-color" content="#3f342a" />
  <meta name="description" content="Compact, aristocratic blog by Yakup Sarıçam.">
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
        const cats = (a.dataset.cat || "").split(',').map(s=>s.trim()).filter(Boolean);
        const subs = (a.dataset.sub || "").split(',').map(s=>s.trim()).filter(Boolean);
        const okCat = !q.cat || cats.includes(q.cat);
        const okSub = !q.sub || subs.includes(q.sub);
        a.style.display = (okCat && okSub) ? "" : "none";
      }});
    }}
    window.addEventListener('hashchange', applyFilter);
    applyFilter();
  </script>
</body>
</html>
"""

def build_index_card_multi(title, cats, date, slug, content) -> str:
    """
    cats: [("Category","Subcategory"), ...]  (Subcategory "" olabilir)
    """
    preview = re.sub(r"\s+", " ", content.strip())[:EXCERPT_LEN] + "…"
    cat_slugs = ",".join(slugify(c) for c, _ in cats if c.strip())
    sub_slugs = ",".join(slugify(s) for _, s in cats if s and s.strip())

    tags = []
    for c, s in cats:
        if c.strip():
            tags.append(f"<a class=\"tag\" href=\"index.html#cat={slugify(c)}\">{escape(c)}</a>")
        if s and s.strip():
            tags.append(f"<a class=\"tag\" href=\"index.html#cat={slugify(c)}&sub={slugify(s)}\">{escape(s)}</a>")
    tags_html = "\n            ".join(tags)

    return f"""
        <article class="card" data-cat="{cat_slugs}" data-sub="{sub_slugs}">
          <div class="date-badge">{escape(date)}</div>
          <div class="meta">
            {tags_html}
          </div>
          <h2 class="title">{escape(title)}</h2>
          <p class="excerpt">{escape(preview)}</p>
          <div class="actions">
            <a class="btn" href="posts/{escape(slug)}.html">Read more</a>
          </div>
        </article>
""".rstrip()

def purge_existing_cards(index_html: str, slug: str) -> str:
    """Aynı sluga giden eski kartları index'ten temizle (Martin Eden'e dokunmaz)."""
    pattern = re.compile(
        r'<article class="card"[\s\S]*?href="posts/' + re.escape(slug) + r'\.html"[\s\S]*?</article>\s*',
        re.IGNORECASE
    )
    return re.sub(pattern, "", index_html)

def main_cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--category", required=True)
    ap.add_argument("--subcategory", required=False, default="", help="Alt kategori opsiyonel; boş bırakılabilir")
    ap.add_argument("--date", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--content_file")
    g.add_argument("--content_text")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--also", action="append", default=[],
                    help="Ek kategori çiftleri: 'Category|Subcategory'. Alt kategori yoksa 'Category|' kullanın.")
    args = ap.parse_args()

    # İçeriği al
    if args.content_file and os.path.exists(args.content_file):
        with open(args.content_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
    elif args.content_text:
        content = args.content_text.strip()
    else:
        print("Error: Provide --content_file or --content_text", file=sys.stderr)
        sys.exit(1)

    # Yol/çıkış
    os.makedirs(os.path.join(args.outdir, "posts"), exist_ok=True)
    menu_html = build_menu_html()
    slug = slugify(args.title)
    post_filename = os.path.join(args.outdir, "posts", f"{slug}.html")
    index_filename = os.path.join(args.outdir, "index.html")

    # index scaffold (yoksa yaz) ve eski kartları temizle
    if os.path.exists(index_filename):
        with open(index_filename, "r", encoding="utf-8") as f:
            current_index = f.read()
    else:
        current_index = ""
    if "<section id=\"list\"" not in current_index:
        current_index = build_index_scaffold(menu_html, SITE_TITLE)

    # Aynı sluga giden tüm eski kartları temizle
    current_index = purge_existing_cards(current_index, slug)

    # Çoklu kategori tek kart
    pairs = [(args.category, args.subcategory or "")]
    for pair in args.also:
        parts = pair.split("|", 1)
        extra_cat = parts[0].strip()
        extra_sub = parts[1].strip() if len(parts) > 1 else ""
        if extra_cat:
            pairs.append((extra_cat, extra_sub))

    card_html = build_index_card_multi(args.title, pairs, args.date, slug, content)

    # YENİ POSTU HER ZAMAN EN ÜSTE EKLE
    marker = '<section id="list">'
    pos = current_index.find(marker)
    if pos != -1:
        updated_index = current_index[:pos+len(marker)] + "\n        " + card_html + current_index[pos+len(marker):]
    else:
        updated_index = current_index.replace("</section>", card_html + "\n      </section>", 1)

    with open(index_filename, "w", encoding="utf-8") as f:
        f.write(updated_index)

    # Post sayfası (tek kez)
    post_html = build_post_html(SITE_TITLE, menu_html, args.title, pairs, args.date, content)
    with open(post_filename, "w", encoding="utf-8") as f:
        f.write(post_html)

    print("Created:", post_filename)
    print("Updated:", index_filename)

if __name__ == "__main__":
    main_cli()