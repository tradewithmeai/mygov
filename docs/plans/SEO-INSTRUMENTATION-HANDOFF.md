# YourGov SEO instrumentation — handoff for a mygov-rooted Claude session

> Written by the solvx-website session (2026-07-17) as part of a site-wide SEO push. It is
> handing YourGov's on-page SEO to a Claude working IN this repo, so the idiomatic route into
> the app and the test/deploy path are correct. **The solvx session did NOT edit any code
> here** — only this doc. Follow this repo's `AGENTS.md` protocol and `docs/KRYSTAL_DEPLOY.md`.

## Why

solvx.uk is being instrumented for organic search. A live audit (`curl`) of
`https://yourgov.solvx.uk/start` found YourGov has **zero on-page SEO**, and it is the
strongest civic asset in the ecosystem (most searchable). Current state:

| tag | status |
|-----|--------|
| `<title>` | **weak — renders just "YourGov"** |
| meta description | ❌ missing |
| canonical | ❌ missing |
| Open Graph (og:*) | ❌ missing |
| Twitter card | ❌ missing |
| JSON-LD schema | ❌ missing |
| `analytics.js` | ✅ present (already injected) |

## What I found about the app's shape (verify before acting)

- `/start` (`app.py:~1503`) is a **302 redirect** into the `/source-lens` shell via
  `_global_entry_url(...)` — so the indexable landing page is that shell, and its title is
  "YourGov". There is **no shared base template** (each of ~26 templates has its own `<head>`).
- The repo already injects site-wide `<head>`/`<body>` snippets with **two `@app.after_request`
  hooks** — `_inject_feedback_link` and `_inject_skip_link` (`app.py:~105` and `~147`). They are
  the proven, safe pattern: path skip-list, `text/html` + `direct_passthrough` guard,
  idempotency check, and a `try/except` that **never breaks a render**. **Mirror this pattern**
  rather than editing 26 templates.

## Recommended change (additive, low-risk)

Add a third `@app.after_request` hook, `_inject_seo_head`, that inserts shared SEO tags right
after the first `<head>`. Additive only; never replaces existing tags; idempotent; wrapped so a
failure returns the untouched response. Skip `/api`, `/static`, `/map/relay` (the embeddable
iframe). Canonical/og:url = `"https://yourgov.solvx.uk" + request.path` (deterministic — do NOT
rely on `request.url_root` behind the proxy). og:image reuses the screenshot already hosted on
the main site: `https://solvx.uk/screenshot-yourgov-map.png`.

```python
_SEO_HEAD_SKIP_PREFIXES = ("/api", "/static", "/map/relay")
_HEAD_OPEN_RE = re.compile(rb"<head\b[^>]*>", re.IGNORECASE)
_SEO_OG_IMAGE = "https://solvx.uk/screenshot-yourgov-map.png"
_SEO_DESC = ("Explore every UK constituency on an interactive map coloured by party, see how "
             "your MP voted, and compare parties in plain English. By solvX.")

@app.after_request
def _inject_seo_head(response):
    try:
        path = request.path or ""
        if any(path == p or path.startswith(p + "/") for p in _SEO_HEAD_SKIP_PREFIXES):
            return response
        ctype = response.headers.get("Content-Type", "")
        if "text/html" not in ctype or response.direct_passthrough:
            return response
        body = response.get_data()
        m = _HEAD_OPEN_RE.search(body)
        if not m or b'property="og:site_name"' in body:  # no <head>, or already injected
            return response
        canonical = "https://yourgov.solvx.uk" + path
        tags = [
            '' if b'name="description"' in body else
                '<meta name="description" content="%s"/>' % _SEO_DESC,
            '<link rel="canonical" href="%s"/>' % canonical,
            '<meta property="og:site_name" content="YourGov by solvX"/>',
            '<meta property="og:type" content="website"/>',
            '<meta property="og:title" content="YourGov — the UK constituency map &amp; MP voting records"/>',
            '<meta property="og:description" content="%s"/>' % _SEO_DESC,
            '<meta property="og:url" content="%s"/>' % canonical,
            '<meta property="og:image" content="%s"/>' % _SEO_OG_IMAGE,
            '<meta name="twitter:card" content="summary_large_image"/>',
            '<meta name="twitter:title" content="YourGov — UK constituency map &amp; MP voting records"/>',
            '<meta name="twitter:image" content="%s"/>' % _SEO_OG_IMAGE,
        ]
        snippet = ("".join(t for t in tags if t)).encode("utf-8")
        response.set_data(body[:m.end()] + snippet + body[m.end():])
    except Exception:
        return response
    return response
```

**Higher-value follow-up (needs your per-shell knowledge):** the real win is a keyword-led
`<title>` on the main entry shell instead of "YourGov" — e.g.
`YourGov — UK Constituency Map & MP Voting Records | solvX`. Because titles must be page-specific
and the shells are yours, do this in the template(s), not the injector. A `WebApplication`
JSON-LD block is also worth adding to the entry shell:

```html
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"WebApplication","name":"YourGov","url":"https://yourgov.solvx.uk/start","applicationCategory":"GovernmentApplication","operatingSystem":"Any (web browser)","description":"Interactive UK constituency map coloured by party with MP voting-record analysis and party comparison.","publisher":{"@type":"Organization","name":"solvX","url":"https://solvx.uk"},"offers":{"@type":"Offer","price":"0","priceCurrency":"GBP"}}
</script>
```

## Target keywords (weave into title/H1/copy where natural — no stuffing)
From the solvx SEO ledger: **"how did my MP vote"**, **"UK constituency map by party"**,
**"my MP by postcode"**, **"Mandelson documents searchable"** (cross-link opportunity).

## Constraints / definition of done
- **Additive only. It is a live app that took a lot of work — never break a render** (the
  `try/except` guarantee above is non-negotiable; keep it).
- Run the test suite (`tests/`) — especially `test_accessibility*.py` — before and after.
- Verify locally: load the `/source-lens` shell and confirm the tags appear in `<head>` and the
  page still renders; confirm `/map/relay` (the iframe) is unaffected.
- Deploy via `docs/KRYSTAL_DEPLOY.md`. Then re-check live with:
  `curl -s https://yourgov.solvx.uk/start | grep -iE 'og:title|canonical|description'`.
- Ready-to-paste blocks + the full multi-subdomain audit live in the website repo at
  `solvx-website/seo/subdomain-fixes.md`; update `solvx-website/seo/PROGRESS.md` when done.
