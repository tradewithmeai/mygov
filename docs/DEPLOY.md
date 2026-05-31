# Deploy

## Vercel

This repo is configured for Vercel with:

- `vercel.json`
- `api/index.py` (imports Flask `app`)

### Required steps

1. Set project root to this repo.
2. Ensure Python runtime is available.
3. Deploy from `main`.

### Runtime behavior

- `mygov.db` is bundled as seed data.
- In serverless runtime, app copies seed DB to `/tmp/mygov.db` for writable usage.

### Environment variables

- `OPENAI_API_KEY` (optional but required for live AI explain path)
- `ASSET_VERSION` (optional cache-busting override)
- `ANALYTICS_DISABLED=1` to disable Vercel analytics injection

## Local verification before deploy

```powershell
python -m pytest tests -q
python scripts/validate_production_ready.py
```

If no local test suite is included in this clean repo revision, verify manually:

- `/source-lens` loads
- `/global` loads
- `/mp/206` loads
- map mode buttons recolor map
- mobile source/map switch works

