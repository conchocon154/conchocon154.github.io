#!/usr/bin/env python3
"""Split the bilingual master into one page per language, plus the crawl files.

src/index.html holds both languages in the same markup, which is comfortable to
edit but poor for search: a crawler reads the English and the Vietnamese
interleaved sentence by sentence, so half of every page is a near-duplicate in
another language and neither version reads cleanly.

This emits one page per language instead —

    /            English   (canonical, x-default)
    /vi/         Vietnamese

— each containing only its own text, declaring its own <html lang>, and pointing
at the other through hreflang so Google serves the right one rather than
guessing. The language button stops being a CSS toggle and becomes an ordinary
link between the two URLs, which also means it works without JavaScript.

Also written: sitemap.xml, robots.txt, llms.txt, and the JSON-LD describing who
the site is about.

Usage:
    python3 tools/build_site.py
    python3 tools/build_site.py --check     # fail if the output is stale
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "src" / "index.html"
BASE = "https://conchocon154.github.io"

# Paste the token from Search Console → Add property → HTML tag (the value of
# the content attribute, not the whole tag) and rebuild. Empty means the meta
# tag is simply not emitted.
GOOGLE_SITE_VERIFICATION = ""

# Everything the pages need to differ on, in one place.
LANGS = {
    "en": {
        "path": "index.html",
        "url": f"{BASE}/",
        "html_lang": "en",
        "og_locale": "en_US",
        "title": "Lê Minh Đăng — Data & Business Analyst | SQL, Python, Ho Chi Minh City",
        "description": (
            "Data and business analyst in Ho Chi Minh City, open to remote work. "
            "SQL, Python and statistics applied to inventory, margin, receivables and "
            "retrieval problems — five public projects, each with a baseline it had to "
            "beat and a significance test it had to survive."
        ),
        "switch_href": "/vi/",
        "switch_label": "VI",
        "switch_aria": "Chuyển sang tiếng Việt",
        "asset_prefix": "",
    },
    "vi": {
        "path": "vi/index.html",
        "url": f"{BASE}/vi/",
        "html_lang": "vi",
        "og_locale": "vi_VN",
        "title": "Lê Minh Đăng — Data & Business Analyst | SQL, Python, TP. Hồ Chí Minh",
        "description": (
            "Chuyên viên phân tích dữ liệu và nghiệp vụ tại TP. Hồ Chí Minh, sẵn sàng làm "
            "remote. SQL, Python và thống kê cho các bài toán tồn kho, biên lợi nhuận, công "
            "nợ và truy hồi thông tin — năm dự án công khai, mỗi dự án đều có mốc so sánh "
            "phải vượt qua và kiểm định thống kê phải đứng vững."
        ),
        "switch_href": "/",
        "switch_label": "EN",
        "switch_aria": "Switch to English",
        "asset_prefix": "../",
    },
}

# --------------------------------------------------------------------------
# structured data — this is what a knowledge panel and an AI answer read
# --------------------------------------------------------------------------

def json_ld(lang: str) -> str:
    cfg = LANGS[lang]
    # json.dumps, not repr: Python's repr emits single quotes, which is not JSON
    # and makes the whole block invisible to a validator.
    desc = json.dumps(cfg["description"], ensure_ascii=False)
    title = json.dumps(cfg["title"], ensure_ascii=False)
    return f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "Person",
      "@id": "{BASE}/#person",
      "name": "Lê Minh Đăng",
      "alternateName": ["Le Minh Dang", "DangLe"],
      "url": "{BASE}/",
      "image": "{BASE}/assets/img/og.png",
      "email": "mailto:dangleminh6677@gmail.com",
      "jobTitle": "Data & Business Analyst",
      "description": {desc},
      "address": {{
        "@type": "PostalAddress",
        "addressLocality": "Ho Chi Minh City",
        "addressCountry": "VN"
      }},
      "alumniOf": {{
        "@type": "CollegeOrUniversity",
        "name": "Ton Duc Thang University",
        "sameAs": "https://en.tdtu.edu.vn/"
      }},
      "knowsLanguage": ["vi", "en", "zh"],
      "knowsAbout": [
        "Data analysis", "Business analysis", "SQL", "Python", "pandas",
        "Statistics", "Logistic regression", "A/B and significance testing",
        "Inventory analytics", "FIFO costing", "Accounts receivable ageing",
        "Information retrieval", "Machine learning", "PyTorch", "Data visualisation"
      ],
      "seeks": {{
        "@type": "Demand",
        "name": "Remote Data Analyst or Business Analyst role"
      }},
      "sameAs": [
        "https://github.com/conchocon154",
        "https://www.kaggle.com/minhngle"
      ]
    }},
    {{
      "@type": "ProfilePage",
      "@id": "{cfg["url"]}#page",
      "url": "{cfg["url"]}",
      "name": {title},
      "description": {desc},
      "inLanguage": "{lang}",
      "mainEntity": {{ "@id": "{BASE}/#person" }},
      "isPartOf": {{ "@id": "{BASE}/#website" }}
    }},
    {{
      "@type": "WebSite",
      "@id": "{BASE}/#website",
      "url": "{BASE}/",
      "name": "Lê Minh Đăng — portfolio",
      "inLanguage": ["en", "vi"],
      "author": {{ "@id": "{BASE}/#person" }}
    }},
    {{
      "@type": "ItemList",
      "@id": "{cfg["url"]}#projects",
      "name": "Selected data projects",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "retail-analytics-sql",
          "description": "Inventory, margin and receivables analysis in SQL over a simulated Vietnamese hardware shop — FIFO costing, ABC concentration, ageing, reorder points.",
          "url": "https://github.com/conchocon154/retail-analytics-sql"}},
        {{"@type": "ListItem", "position": 2, "name": "vn-product-matcher",
          "description": "Matching free-text Vietnamese product names onto catalogue SKUs; a fine-tuned encoder reaches 96.9% Recall@1 on unseen SKUs against measured lexical baselines.",
          "url": "https://github.com/conchocon154/vn-product-matcher"}},
        {{"@type": "ListItem", "position": 3, "name": "ev-purchase-analysis",
          "description": "What decides an electric-vehicle purchase, over 668,665 records — including an apparent interaction that a likelihood ratio test rejected.",
          "url": "https://github.com/conchocon154/ev-purchase-analysis"}},
        {{"@type": "ListItem", "position": 4, "name": "caption-decoding-study",
          "description": "A controlled comparison of beam widths for CNN-LSTM image captioning on MS-COCO, with paired bootstrap significance testing.",
          "url": "https://github.com/conchocon154/caption-decoding-study"}}
      ]
    }}
  ]
}}
</script>"""


# --------------------------------------------------------------------------
# page assembly
# --------------------------------------------------------------------------

def strip_other_language(html: str, keep: str) -> str:
    """Remove every <span lang="…"> belonging to the language we are not keeping."""
    drop = "vi" if keep == "en" else "en"

    # A regex cannot do this: the spans contain inline markup including nested
    # <span>s, so the closing tag is found by counting opens and closes.
    out = []
    i = 0
    open_tag = f'<span lang="{drop}">'
    while True:
        j = html.find(open_tag, i)
        if j == -1:
            out.append(html[i:])
            break
        out.append(html[i:j])
        depth = 0
        k = j
        while k < len(html):
            nxt_open = html.find("<span", k)
            nxt_close = html.find("</span>", k)
            if nxt_close == -1:
                raise SystemExit("unbalanced <span> in master")
            if nxt_open != -1 and nxt_open < nxt_close:
                depth += 1
                k = nxt_open + 5
            else:
                depth -= 1
                k = nxt_close + 7
                if depth == 0:
                    break
        i = k
    return "".join(out)


def build(lang: str, master: str) -> str:
    cfg = LANGS[lang]
    other = "vi" if lang == "en" else "en"
    p = cfg["asset_prefix"]
    s = strip_other_language(master, lang)

    # --- <html> attributes: the language toggle is now a URL, not a state
    s = s.replace('<html lang="en" data-theme="dark" data-lang="en">',
                  f'<html lang="{cfg["html_lang"]}" data-theme="dark">')

    # --- head
    s = s.replace("<title>Lê Minh Đăng — Data &amp; Business Analyst</title>",
                  f"<title>{cfg['title']}</title>")
    s = re.sub(r'<meta name="description" content="[^"]*">',
               f'<meta name="description" content="{cfg["description"]}">', s)
    s = re.sub(r'<meta property="og:title" content="[^"]*">',
               f'<meta property="og:title" content="{cfg["title"]}">', s)
    s = re.sub(r'<meta property="og:description" content="[^"]*">',
               f'<meta property="og:description" content="{cfg["description"]}">', s)
    s = s.replace('<meta property="og:url" content="https://conchocon154.github.io/">',
                  f'<meta property="og:url" content="{cfg["url"]}">')

    verify = (f'<meta name="google-site-verification" content="{GOOGLE_SITE_VERIFICATION}">\n'
              if GOOGLE_SITE_VERIFICATION else "")
    head_extra = f"""{verify}<link rel="canonical" href="{cfg['url']}">
<link rel="alternate" hreflang="en" href="{LANGS['en']['url']}">
<link rel="alternate" hreflang="vi" href="{LANGS['vi']['url']}">
<link rel="alternate" hreflang="x-default" href="{LANGS['en']['url']}">
<meta property="og:locale" content="{cfg['og_locale']}">
<meta property="og:locale:alternate" content="{LANGS[other]['og_locale']}">
<meta property="og:site_name" content="Lê Minh Đăng">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
"""
    s = s.replace('<link rel="stylesheet" href="assets/css/style.css">',
                  head_extra + json_ld(lang) + f'\n<link rel="stylesheet" href="{p}assets/css/style.css">')

    # --- asset paths for the nested page
    if p:
        s = s.replace('href="assets/', f'href="{p}assets/')
        s = s.replace('src="assets/', f'src="{p}assets/')
        s = s.replace('content="https://conchocon154.github.io/assets/',
                      'content="https://conchocon154.github.io/assets/')  # absolute already
        # in-page anchors keep working only if they point at this page
        s = re.sub(r'href="#([\w-]+)"', r'href="#\1"', s)

    # --- the language control becomes a link between the two URLs
    old_btn = re.search(
        r'<button class="tg" id="langBtn".*?</button>', s, re.DOTALL)
    if not old_btn:
        raise SystemExit("language button not found in master")
    new_btn = (
        f'<a class="tg" id="langBtn" href="{cfg["switch_href"]}" '
        f'hreflang="{other}" aria-label="{cfg["switch_aria"]}" rel="alternate">'
        f'<svg class="ico"><use href="#i-globe"/></svg>'
        f'<span class="tg-label">{cfg["switch_label"]}</span></a>'
    )
    s = s[:old_btn.start()] + new_btn + s[old_btn.end():]

    s = s.replace("<!-- GENERATED -->", "")
    banner = ("<!-- Generated from src/index.html by tools/build_site.py — edit the "
              "master, not this file. -->\n")
    return banner + s


# --------------------------------------------------------------------------
# crawl files
# --------------------------------------------------------------------------

def sitemap() -> str:
    today = date.today().isoformat()
    entries = []
    for lang, cfg in LANGS.items():
        alts = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{c["url"]}"/>'
            for l, c in LANGS.items()
        )
        alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{LANGS["en"]["url"]}"/>'
        entries.append(
            f'  <url>\n    <loc>{cfg["url"]}</loc>\n    <lastmod>{today}</lastmod>'
            f'\n    <changefreq>monthly</changefreq>'
            f'\n    <priority>{"1.0" if lang == "en" else "0.9"}</priority>{alts}\n  </url>'
        )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
            '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(entries) + "\n</urlset>\n")


def robots() -> str:
    # Assistants are a real referral path for a portfolio, so they are named
    # explicitly rather than left to the default.
    ai = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User",
          "Claude-SearchBot", "anthropic-ai", "PerplexityBot", "Perplexity-User",
          "Google-Extended", "Applebot-Extended", "CCBot", "Bingbot", "DuckDuckBot"]
    blocks = "\n\n".join(f"User-agent: {a}\nAllow: /" for a in ai)
    return (f"User-agent: *\nAllow: /\n\n{blocks}\n\n"
            f"Sitemap: {BASE}/sitemap.xml\n")


def llms_txt() -> str:
    return f"""# Lê Minh Đăng

> Data & Business Analyst based in Ho Chi Minh City, Vietnam, open to remote
> roles. Computer Science graduate of Ton Duc Thang University (2025). Works in
> SQL, Python and applied statistics on inventory, margin, receivables and
> information-retrieval problems.

Contact: dangleminh6677@gmail.com · {BASE}/

## What distinguishes this work

Every public project carries a baseline it had to beat and a significance test
it had to survive, and the negative results are published rather than dropped:
a hybrid reranker that changed nothing (p = 1.00), an interaction effect that a
likelihood ratio test rejected (p = 0.62), and a Kaggle submission that placed
398 of 471. The write-ups state these plainly.

## Pages

- [Portfolio (English)]({LANGS['en']['url']}): case studies with the figures, methods and caveats
- [Portfolio (Tiếng Việt)]({LANGS['vi']['url']}): the same in Vietnamese

## Projects

- [retail-analytics-sql](https://github.com/conchocon154/retail-analytics-sql): eight analytical SQL queries over a simulated Vietnamese hardware shop — FIFO gross margin, ABC concentration, inventory turnover, receivables ageing, reorder points; 20 tests.
- [vn-product-matcher](https://github.com/conchocon154/vn-product-matcher): matches free-text Vietnamese hardware names onto 1,827 catalogue SKUs; fine-tuned multilingual encoder reaches 96.9% Recall@1 on held-out SKUs, 1.9 points over a TF-IDF baseline (McNemar p = 1.2e-3).
- [ev-purchase-analysis](https://github.com/conchocon154/ev-purchase-analysis): bilingual analysis of 668,665 records on electric-vehicle purchase decisions; logistic regression at 0.938 AUC chosen over a 0.941 gradient-boosted model for interpretability.
- [caption-decoding-study](https://github.com/conchocon154/caption-decoding-study): controlled comparison of beam widths for CNN-LSTM image captioning on MS-COCO; BLEU-4 peaks at beam 5 and falls at beam 10 (p = 0.017) while caption diversity declines throughout.
- [object-detection](https://github.com/conchocon154/object-detection): real-time detection pipeline with YOLO and OpenCV.

## Skills

SQL · SQLite · MySQL · Python · pandas · NumPy · statsmodels · scikit-learn ·
PyTorch · FastAPI · pytest · Git · GitHub Actions · matplotlib · Jupyter ·
logistic regression · gradient boosting · McNemar and bootstrap significance
testing · FIFO costing · cohort and ageing analysis

## Languages

Vietnamese (native) · English (PET B1) · Chinese (conversational)
"""


# --------------------------------------------------------------------------

def not_found() -> str:
    """GitHub Pages serves this for any unknown path."""
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found — Lê Minh Đăng</title>
<meta name="robots" content="noindex, follow">
<link rel="stylesheet" href="/assets/css/style.css">
<style>
  .nf {{ min-height: 78vh; display: flex; flex-direction: column;
        align-items: flex-start; justify-content: center; }}
  .nf h1 {{ font-size: clamp(34px, 6vw, 58px); margin: 10px 0 0; }}
  .nf p {{ color: var(--text-dim); margin: 14px 0 0; max-width: 46ch; }}
</style>
</head>
<body>
<div class="wrap nf">
  <p class="eyebrow">404</p>
  <h1>That page isn't here</h1>
  <p>The link may be old, or the address slightly off. Everything lives on one page.</p>
  <div class="cta">
    <a class="btn btn-primary" href="/">Go to the portfolio</a>
    <a class="btn" href="/vi/">Tiếng Việt</a>
  </div>
</div>
</body>
</html>
"""


def outputs() -> dict[str, str]:
    master = MASTER.read_text(encoding="utf-8")
    files = {cfg["path"]: build(lang, master) for lang, cfg in LANGS.items()}
    files["sitemap.xml"] = sitemap()
    files["robots.txt"] = robots()
    files["llms.txt"] = llms_txt()
    files["404.html"] = not_found()
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    files = outputs()
    stale = []
    for rel, content in files.items():
        target = ROOT / rel
        # the sitemap stamps today's date, so it is never a staleness signal
        if rel == "sitemap.xml" and target.exists():
            old = re.sub(r"<lastmod>[^<]*</lastmod>", "", target.read_text(encoding="utf-8"))
            new = re.sub(r"<lastmod>[^<]*</lastmod>", "", content)
            if old != new:
                stale.append(rel)
            continue
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            stale.append(rel)

    if args.check:
        if stale:
            print("stale: " + ", ".join(stale) + "\nrun: python3 tools/build_site.py")
            return 1
        print("site up to date")
        return 0

    for rel, content in files.items():
        target = ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    print("wrote " + ", ".join(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
