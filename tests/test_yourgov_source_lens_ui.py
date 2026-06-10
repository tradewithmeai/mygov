import importlib
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _client():
    appmod = importlib.import_module("app")
    appmod.app.config["TESTING"] = True
    return appmod.app.test_client()


def _source_lens_html():
    response = _client().get("/source-lens")
    assert response.status_code == 200
    return response.get_data(as_text=True)


def _panel_js():
    return (ROOT / "static" / "panel_test.js").read_text(encoding="utf-8")


def test_source_lens_renders_yourgov_shell():
    html = _source_lens_html()

    assert "YourGov" in html
    assert "MyGov Lens POC" not in html
    assert 'id="yourgov-panel"' in html
    assert 'id="map-frame"' in html
    assert 'id="source-view-select"' in html
    assert 'value="yourgov-summary"' in html
    assert 'value="publicwhip-record"' in html
    assert 'data-mode="rebel-split"' in html


def test_source_dropdown_defaults_to_yourgov_summary():
    html = _source_lens_html()

    assert re.search(
        r'<option[^>]+value="yourgov-summary"[^>]+selected[^>]*>\s*YourGov Summary\s*</option>',
        html,
    )


def test_panel_js_uses_selected_division_map_endpoint():
    js = _panel_js()

    assert "selectedDivisionId" in js
    assert "/api/lens/division/" in js
    assert "/map?mode=" in js
    assert "/api/lens/map/party" not in js
    assert "/api/lens/map/gender" not in js
    assert "/api/lens/map/rebel-rate" not in js
    assert "ensurePublicWhipLoaded();" not in js
