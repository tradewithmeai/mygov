# Future Plans and Wants

Last updated: 2026-05-31
Owner: MyGov product team

## Priority now

1. Add `Seniority display` from the working A/B map flow into the main user journey.
2. Define where seniority appears:
   - map tooltip
   - MP summary card
   - compare/variant panel
3. Keep it source-linked and caveated (no implied value judgement).

## Short-term roadmap

1. Standardise A/B map variants into one runtime switch with stable telemetry keys.
2. Final UI polish pass for `source-lens`:
   - control alignment
   - label readability
   - mobile interaction consistency
3. Add production validation script in this repo (`scripts/validate_production_ready.py`) and wire into CI.

## Product wants

1. Improve explanation quality controls (Skim vs Detailed) with deterministic fallback behavior.
2. Strengthen link integrity checks:
   - MP routes
   - division source links
   - cross-panel navigation
3. Add lightweight performance budget checks for map render and panel load.

## Stretch wants

1. API-first visualization payloads for third-party embedding.
2. Country-adapter starter flow for non-UK rollouts (doc + scaffold + constraints).
3. Reusable “guided tour” spec that can be turned on/off per route.

## Notes

- This file is planning-only. It does not override red-team constraints.
- Any scoring/ranking language must remain evidence-first and caveated.
