# conchocon154.github.io

Source for my portfolio at **https://conchocon154.github.io**.

No framework, no build step for the page itself, no tracker. One HTML file, one
stylesheet, one small script.

```
index.html              the whole page
assets/css/style.css    theme tokens, layout
assets/js/main.js       theme + language toggles, scroll progress, reveals
assets/img/og.png       social preview card
tools/build_charts.py   regenerates every chart from the project data
tools/og-template.html  source for the preview card
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

## Bilingual

Both languages are in the markup. The toggle flips a `data-lang` attribute on
`<html>` and CSS hides the other one, so switching costs no reflow of content
that has to be fetched. The theme toggle works the same way with `data-theme`,
defaulting to the visitor's system preference.

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
