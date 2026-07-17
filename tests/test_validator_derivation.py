"""Regression tests for check_division_derivation in scripts/validate_production_ready.py.

The check proves the per-division map modes actually vary by division (not a constant
national map). It used to compare only against the single preceding division and
hard-fail if they matched — which false-failed the whole daily refresh whenever the
two latest divisions shared a lobby (e.g. two back-to-back votes carried by the same
MPs, as happened 2026-07-15 with divisions 2410/2411). The fix compares against
several recent divisions and passes a mode as soon as any of them differs.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import validate_production_ready as vp


def _run(monkeypatch, maps, recent):
    monkeypatch.setattr(vp, "_recent_division_ids", lambda client, primary, limit=12: list(recent))
    monkeypatch.setattr(vp, "_mode_category_map", lambda client, div_id, mode: dict(maps[div_id]))
    v = vp.Validation()
    vp.check_division_derivation(v, client=None, division_id=2411)
    return v


def test_passes_when_a_later_division_differs_even_if_adjacent_is_identical(monkeypatch):
    # 2410 is byte-identical to 2411 (the real 2026-07-15 case); 2409 differs.
    maps = {
        2411: {"A": "aye", "B": "no"},
        2410: {"A": "aye", "B": "no"},   # identical adjacent division
        2409: {"A": "no", "B": "aye"},   # a genuinely different division
    }
    v = _run(monkeypatch, maps, recent=[2410, 2409])
    assert v.failures == []  # all four modes find a contrast -> PASS


def test_fails_when_identical_across_all_recent_divisions(monkeypatch):
    # The genuine red flag the check exists to catch: a constant national map.
    maps = {2411: {"A": "x"}, 2410: {"A": "x"}, 2409: {"A": "x"}}
    v = _run(monkeypatch, maps, recent=[2410, 2409])
    assert len(v.failures) == 4  # every mode identical across every comparison


def test_passes_trivially_when_no_other_division_available(monkeypatch):
    monkeypatch.setattr(vp, "_recent_division_ids", lambda client, primary, limit=12: [])
    v = vp.Validation()
    vp.check_division_derivation(v, client=None, division_id=2411)
    assert v.failures == []


def test_first_differing_candidate_is_used_as_contrast(monkeypatch):
    # Confirms it stops at the first differing division (2409), not a later one.
    maps = {
        2411: {"A": "aye"},
        2410: {"A": "aye"},   # identical -> skipped
        2409: {"A": "no"},    # first differing -> chosen
        2408: {"A": "no"},
    }
    v = _run(monkeypatch, maps, recent=[2410, 2409, 2408])
    assert v.failures == []
