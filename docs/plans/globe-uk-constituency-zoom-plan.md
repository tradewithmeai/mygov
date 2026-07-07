# Plan: Combined Globe + UK Constituency Map Asset

Status: PLAN ONLY — no implementation yet. Additive changes only. Build on branch `feature/globe-uk-constituency-zoom`.

## Goal

A new asset at `/globe-map` that combines the existing globe (`/global`, `static/global_globe.js`, Three.js) with the existing promap 2D constituency map (`/map/pro`, prebuilt React/Leaflet bundle in `static/promap/`).

- UK constituency boundaries rendered geographically correct on the globe surface.
- Globe controls identical to `/global` (drag yaw/pitch, wheel zoom, arrow keys, idle north-up spin, search, legend filters, feasibility markers).
- Clicking the UK landmass zooms in and transitions to the full promap, embedded via iframe so it behaves *exactly* as it does at `/map/pro` today.
- Existing assets (`/global`, `/map`, `/map/pro`, `/map/relay`) untouched.

## Constraints honoured

- **Additive only.** New files + one appended route in `app.py`. No existing line modified or deleted.
- **Live repo.** New page is only reachable by its URL; no nav links added (adding links would modify existing templates — deferred to a follow-up).
- **Behaviour parity.** Globe interactions copied from `global_globe.js` verbatim patterns; 2D map embedded, not re-implemented.

## New files

| File | Purpose |
|---|---|
| `templates/globe_map.html` | New page. Same shell structure as `global.html` (stage, tooltip, search, legend, stat cards, country card) plus a hidden full-screen overlay `<div>` containing `<iframe src="/map/pro">` and a parent-owned "Back to globe" button. |
| `static/globe_map.js` | New ES module. Copies the globe implementation patterns from `global_globe.js` (Three.js 0.164.1 CDN, `latLonToVector3`, globeGroup/spinGroup split, same clamps and speeds) and adds the UK layer + zoom transition. `global_globe.js` is not modified. |
| `static/globe_map.css` | Styles for the new page (based on `global_globe.css`, new classnames). |
| `scripts/build_globe_constituency_layer.py` | One-off generator. Reads `static/promap/data/constituencies-uk-2024-bgc.geojson` (11 MB, 650 features, EPSG:4326), simplifies rings (~0.004–0.006° tolerance, 4 dp quantisation), strips properties to `{code, name, centroidLat, centroidLong}`. Also emits a dissolved UK outline for hit-testing. Size budget: < 1 MB combined. |
| `static/data/geo/constituencies-uk-2024-globe.geojson` | Generated simplified constituency boundaries for the globe layer (checked in, like other generated data). |
| `static/data/geo/uk-outline-globe.geojson` | Generated dissolved UK outline for click hit-testing. |
| `tests/test_globe_map.py` | New tests (below). |

## Appended route (only change to an existing file)

```python
@app.route("/globe-map")
def globe_map():
    return render_template("globe_map.html")
```

## How it works

### 1. Globe (parity with /global)
Identical setup: camera z 7.25, wheel clamp 5.4–10.2, drag rotation clamps ±1.15 rad, idle spin 0.0017 rad/frame on `spinGroup`, world-atlas 110m borders from CDN at radius +0.012, feasibility markers from `/api/global/feasibility`, search/legend/country-card logic unchanged. Marker clicks behave exactly as today (select; navigate to source-lens when `working_adapter`).

### 2. UK constituency layer on the globe
- Fetch `constituencies-uk-2024-globe.geojson`; build a single `THREE.LineSegments` with the existing `latLonToVector3` at radius +0.014 (just above country borders — same technique, so geographic correctness is by construction: same sphere mapping as the world borders).
- One geometry, one draw call — ~650 simplified polygons is cheap.
- Distance-based fade: layer opacity ramps up as `camera.position.z` drops below ~7 so far-out views stay uncluttered.
- Hover over UK landmass (not on a marker): highlight layer, `cursor:pointer`, tooltip "United Kingdom — click to open the constituency map".

### 3. Click-to-zoom transition
- Click handler order: marker raycast first (existing behaviour wins), else raycast the earth sphere → convert hit point to lat/lon → point-in-polygon against the dissolved UK outline.
- On UK hit: reuse the `focusCountryOnGlobe` yaw/pitch animation to centre UK (lat 54.6, lon −2.9), then dolly camera z 7.25 → ~3.2 (transition-only; user wheel clamp stays 5.4–10.2 so control feel is unchanged) while constituency lines fade to full opacity.
- At the end of the dolly, crossfade in the overlay containing the promap iframe (preloaded hidden at page load, so the swap is instant). The promap runs its own untouched bundle — full interactivity guaranteed.
- Exit: parent-owned "Back to globe" button (and Escape in the parent document) fades the overlay out and animates the camera back to default framing; idle spin resumes.

### 4. What we do NOT touch
- `static/promap/**` (prebuilt bundle, source in separate project)
- `templates/global.html`, `static/global_globe.js`, `templates/map.html`, `templates/map_relay.html`
- Existing routes and APIs

## Verification

1. `tests/test_globe_map.py`:
   - `/globe-map` returns 200 and contains the stage + iframe container markers.
   - Generated GeoJSON: valid JSON, 650 features, all `PCON24CD` codes present, coords within UK bbox (−9..2 lon, 49..61 lat), file size under budget.
   - Existing routes `/global`, `/map`, `/map/pro`, `/map/relay` still 200 (regression guard).
2. Run the full existing test suite — must be green (nothing existing modified).
3. Manual browser pass on the dev server:
   - Globe parity checklist vs `/global`: drag, wheel, arrows, idle spin, search, legend filters, marker hover/click.
   - UK hover → click → zoom → promap loads and is fully interactive (pan, zoom, constituency click, colour modes).
   - Back button returns to the globe with controls intact.
4. `python scripts/verify_agent_tour.py` still passes (tour untouched).

## Risks & mitigations

- **11 MB GeoJSON on the globe** — never loaded there; the simplified generated layer is mandatory.
- **Z-fighting of lines on sphere** — radius offset +0.014 and `depthWrite` handling, same as existing borders.
- **Iframe load failure** — overlay shows a fallback link to `/map/pro`; globe remains usable.
- **CDN dependencies** (three.js, world-atlas) — same as `/global` today; no new CDN deps added.

## Branch & commits

Branch `feature/globe-uk-constituency-zoom`:
1. `scripts/build_globe_constituency_layer.py` + generated geo files
2. `templates/globe_map.html` + `static/globe_map.css` + `static/globe_map.js`
3. `app.py` appended route + `tests/test_globe_map.py`

Follow-up (separate, non-additive PR if desired): nav links from `/global` and `/start` to the new asset.
