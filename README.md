# conchocon154.github.io

Source for my portfolio at **https://conchocon154.github.io**.

No framework, no build step for the page itself, no tracker. One HTML file, one
stylesheet, one small script.

```
src/index.html          bilingual master — the file to edit
index.html              generated: English page  (canonical)
vi/index.html           generated: Vietnamese page
sitemap.xml robots.txt llms.txt   generated
assets/css/style.css    theme tokens, layout
assets/js/main.js       theme toggle, scroll progress, reveals
assets/img/og.png       social preview card
tools/build_charts.py   regenerates every chart from the project data
tools/build_site.py     splits the master into the two language pages
tools/og-template.html  source for the preview card
```

Edit `src/index.html`, then run both generators:

```bash
python3 tools/build_charts.py && python3 tools/build_site.py
```

## The charts are generated, not drawn

Every figure in the case studies is inline SVG produced by
`tools/build_charts.py`, which reads the CSV and JSON that the four project
repositories emit — so a number on the page traces back to the run that
produced it, and nothing is transcribed by hand.

SVG rather than exported bitmaps for three reasons: it stays sharp at any zoom,
it weighs a fraction of a PNG, and because every fill and stroke is a CSS
custom property, one figure serves both the light and the dark theme instead of
needing two exports.

Regenerating needs the four source repositories checked out beside this one:

```bash
python3 tools/build_charts.py          # rewrite the <!-- CHART:… --> blocks
python3 tools/build_charts.py --check  # fail if index.html is out of date
```

The social card is rendered the same way, from `tools/og-template.html`:

```bash
chrome --headless --window-size=1200,630 --screenshot=assets/img/og.png tools/og-template.html
```

## Bilingual, as two pages rather than one

The master holds both languages in the same markup, which is comfortable to
edit. Shipping it that way was not: a crawler reads the English and the
Vietnamese interleaved sentence by sentence, so half of the page is a
near-duplicate in another language and neither version reads cleanly.

`tools/build_site.py` therefore emits one page per language — `/` in English
(canonical and `x-default`) and `/vi/` in Vietnamese — each carrying only its
own text, declaring its own `<html lang>`, and pointing at the other through
`hreflang`. The language button is an ordinary link between the two URLs, so it
works with JavaScript switched off.

The theme toggle is still runtime state: it flips `data-theme` on `<html>` and
defaults to the visitor's system preference.

## Search and assistants

Each page carries JSON-LD describing the person, the profile page, the site and
the four projects — that is what a knowledge panel and an assistant's answer
read, rather than the prose. `robots.txt` names the assistant crawlers
explicitly instead of leaving them to the default, and `llms.txt` gives them a
short plain-text summary of who this is and what the projects measured.

CI checks that the generated pages match the master, that no stray language
leaked into either one, that the JSON-LD parses, and that the sitemap lists
both pages.

## Local preview

```bash
python3 -m http.server 8080
```

## Projects featured

| Repository | What it is |
|---|---|
| [retail-analytics-sql](https://github.com/conchocon154/retail-analytics-sql) | Inventory, margin and receivables analysis in SQL |
| [vn-product-matcher](https://github.com/conchocon154/vn-product-matcher) | Vietnamese free-text product names → catalogue SKUs |
| [ev-purchase-analysis](https://github.com/conchocon154/ev-purchase-analysis) | What decides an EV purchase — bilingual analysis |
| [caption-decoding-study](https://github.com/conchocon154/caption-decoding-study) | How wide a beam is too wide for image captioning |
