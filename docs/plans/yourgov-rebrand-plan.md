# YourGov Rebrand Plan (Web App)

**Status:** planning · **Scope:** web app only · **Deploy:** staged on a branch → review → Krystal
**Date:** 2026-07-20

## Decisions (locked)

| Question | Decision |
|---|---|
| Wordmark casing | **Hybrid** — logo asset reads `Yourgov` (capital Y, lowercase rest); all visible copy, metadata, JSON-LD, alt text stay **`YourGov`**. No product-wide casing sweep. |
| Palette / theme | **One canonical dark brand** = refined `theme-quiet` (off-white text `#e8eaf0`, civic-cyan accent `#7dd3fc`, source-green `#22c55e`). Make it the default. |
| Theme picker | Keep the mechanism; make the brand theme the default. Glass/editorial retained but de-emphasised (revisit retiring them after the reskin lands). |
| Typography | Self-host **Nunito** (700/800/900) for the logo + `--font-display` (headings/titles). Body stays Inter/system (`--font-body`). |
| Scope | Web only. Mobile apps, social/OG imagery, and docs casing are explicitly **out of this pass**. |

## Canonical identity

- **Logo (primary):** `Yourgov` in Nunito ExtraBold (800), off-white `#e8eaf0`, tight tracking (≈ −0.03em), with a filled **green dot `#22c55e`** on the baseline after the word. White-on-transparent — sits on the dark app surface. (Final asset comes from Claude Design; the vectorised black/outline variants already built in `logo-preview/` are the fallback/reference.)
- **Brand colours:**
  - surface `--bg #0a0e1a`, panel `--panel #0f1626` / `--panel-2 #0d1322`, line `rgba(148,163,184,0.18)`
  - text `--text #e8eaf0`, muted `--muted #94a3b8`
  - accent (civic-cyan) `--accent #7dd3fc`
  - vote colours: aye/green `--aye #22c55e`, no/red `--no #ef4444`, unknown `--unknown #6b7280`
- **Type:** display/brand = Nunito; body = Inter/system.

## What the rebrand touches (surface audit)

- **Tokenised & easy:** `static/panel_test.css` `:root` drives the whole source-lens app via CSS custom properties. Reskin = edit tokens + set default theme.
- **Partially hardcoded (rebrand debt):** `static/lens.css`, `static/publicwhip.css`, `static/globe_map.css`, `static/global_globe.css`, `static/explain-mode.css`, `static/demo-flow.css` — contain literal hex/fonts; migrate to tokens.
- **Compiled, out of scope:** `static/promap/**` is a prebuilt Vite bundle; can't be reskinned without its source. Note as a known inconsistency; theme it later from source or wrap it.
- **Assets:** `static/img/yourgov-logo.svg` (wordmark), `yourgov-mark.svg` (square mark), `favicon.svg`, plus the OG/social image referenced by the SEO `<head>` tags.
- **Fonts:** no Nunito today — must be self-hosted (CSP blocks font CDNs; Passenger host is effectively offline). Subset to Latin + the weights used.
- **Tests that move with the brand:** `tests/test_yourgov_branding.py` (asserts `YourGov` visible copy — stays true under hybrid; asserts the 3 SVG assets exist + contain `yourgov`/`yg`, no `crown`/`gov.uk`), `tests/test_yourgov_source_lens_ui.py` (favicon link, asset serving, logo referenced in the explainer prompt), `tests/test_seo_head.py` (OG/twitter/canonical).

## Phased plan

### Phase 0 — Branch + baseline
- Branch `rebrand-web` off `main`. Capture before/after screenshots of key routes (`/source-lens`, `/global`, `/welcome`, `/publicwhip`, `/map`, `/map/pro`).
- Run the full suite green first (baseline).

### Phase 1 — Foundations (tokens + fonts)
- Self-host Nunito (700/800/900, Latin subset) under `static/fonts/`; add `@font-face` (not a CDN link). Confirm the deploy bundle ships `static/fonts/**` (`cp -R static` already covers it — verify).
- Introduce a brand token layer: promote refined `theme-quiet` values to the default `:root`, set `--font-display` to Nunito. Keep the theme classes working.
- Make the brand theme the initial theme (the inline no-flash `<head>` setter + `theme-picker.js` default).

### Phase 2 — Logo & icon assets
- Drop in the new **white wordmark** `yourgov-logo.svg` (transparent bg) from Claude Design; keep `alt="YourGov"` (hybrid casing).
- New **favicon** + **square mark** in the new identity (compact mark — e.g. the green dot / `Y` monogram). **Dependency on Claude Design** for these two; the wordmark alone can't be a favicon.
- New **OG/social image** (1200×630) on the dark surface with the wordmark. Wire into the SEO `_inject_seo_head` og:image / twitter:image.
- Verify `yg-intro-logo` sizing (`static/panel_test.js:365`, 184×49) against the new aspect ratio; adjust width/height.

### Phase 3 — De-hardcode the remaining stylesheets
- Migrate `lens.css`, `publicwhip.css`, `globe_map.css`, `global_globe.css`, `explain-mode.css`, `demo-flow.css` off literal colours onto the shared tokens. This is where most of the manual work is.
- Re-check AA contrast on the new palette (the existing tokens carry contrast notes; keep them true — vote text `--aye/--no` on panels).

### Phase 4 — Typography rollout
- Apply `--font-display` (Nunito) to headings/titles/section labels across templates; leave dense records/tables on `--font-body`.
- Tune weights/tracking to match the wordmark voice.

### Phase 5 — Tests, a11y, QA
- Update/extend `test_yourgov_branding.py` for the new assets (still `YourGov` copy; new logo content). Keep `test_seo_head.py` green (new og:image).
- WCAG AA contrast pass on the new tokens (ties into the existing accessibility plan's NEXT tier).
- Visual QA across routes + the theme picker; cross-browser sanity.

### Phase 6 — Staged deploy
- Push `rebrand-web`, open a PR, review screenshots. **Do not merge to `main` without sign-off** (main is live).
- Merge (regular merge, no squash), trigger the Krystal deploy, post-deploy live-verify the key routes + favicon + OG.

## Open items / dependencies
- **Claude Design deliverables:** final white wordmark SVG, favicon, square mark, OG image.
- **Picker fate:** decide after Phase 3 whether to retire glass/editorial (less QA surface) or keep them.
- **promap bundle:** left on the old look this pass; schedule a source-level reskin separately.
- **Mobile + docs casing:** deferred to a later pass (explicitly out of scope here).

## Risks
- Live site — every phase is branch-first, screenshot-reviewed, deploy-gated.
- Font weight/size shipping cost — subset aggressively.
- Hardcoded-colour migration can cause subtle regressions — do it stylesheet-by-stylesheet with visual diffs.
