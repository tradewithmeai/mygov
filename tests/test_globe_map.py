import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO_DIR = os.path.join(REPO_ROOT, "static", "data", "geo")
CONSTITUENCIES = os.path.join(GEO_DIR, "constituencies-uk-2024-globe.geojson")
OUTLINE = os.path.join(GEO_DIR, "uk-outline-globe.geojson")

# The layer must stay light enough to ship to the globe page on every load.
MAX_CONSTITUENCY_BYTES = 1_500_000
MAX_OUTLINE_BYTES = 100_000

UK_LON_MIN, UK_LON_MAX = -9.0, 2.5
UK_LAT_MIN, UK_LAT_MAX = 49.0, 61.5


def _walk_coords(coords, fn):
    if coords and isinstance(coords[0], (int, float)):
        fn(coords)
        return
    for item in coords:
        _walk_coords(item, fn)


class GlobeMapRouteTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_globe_map_returns_200(self):
        r = self.client.get("/globe-map")
        self.assertEqual(r.status_code, 200)

    def test_globe_map_contains_stage_and_overlay(self):
        body = self.client.get("/globe-map").get_data(as_text=True)
        self.assertIn('id="globe-stage"', body)
        self.assertIn('id="uk-map-overlay"', body)
        self.assertIn('id="uk-map-frame"', body)
        self.assertIn('id="uk-map-back"', body)

    def test_globe_map_points_at_promap_and_geo_layer(self):
        body = self.client.get("/globe-map").get_data(as_text=True)
        self.assertIn('data-map-url="/map/pro"', body)
        self.assertIn("constituencies-uk-2024-globe.geojson", body)
        self.assertIn("uk-outline-globe.geojson", body)
        self.assertIn("globe_map.js", body)

    def test_globe_map_reuses_global_stylesheet(self):
        # Visual parity with /global comes from sharing its stylesheet.
        body = self.client.get("/globe-map").get_data(as_text=True)
        self.assertIn("global_globe.css", body)
        self.assertIn("globe_map.css", body)

    # ── regression guards: the combined asset must not disturb the originals ──

    def test_existing_assets_unchanged(self):
        for route in ("/global", "/map", "/map/pro", "/map/relay"):
            r = self.client.get(route)
            self.assertEqual(r.status_code, 200, f"{route} regressed")

    def test_global_page_does_not_reference_new_asset(self):
        # /global must be byte-for-byte unaware of the new page (additive-only).
        body = self.client.get("/global").get_data(as_text=True)
        self.assertNotIn("globe_map", body)
        self.assertNotIn("uk-map-overlay", body)


class GlobeMapGeoDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(CONSTITUENCIES, encoding="utf-8") as fh:
            cls.constituencies = json.load(fh)
        with open(OUTLINE, encoding="utf-8") as fh:
            cls.outline = json.load(fh)

    def test_constituency_layer_has_all_650_seats(self):
        feats = self.constituencies["features"]
        self.assertEqual(len(feats), 650)
        codes = {f["properties"]["code"] for f in feats}
        self.assertEqual(len(codes), 650)
        self.assertTrue(all(c and c[0] in "ENSW" for c in codes))

    def test_constituency_features_have_names_and_centroids(self):
        for feat in self.constituencies["features"]:
            props = feat["properties"]
            self.assertTrue(props.get("name"))
            self.assertIsNotNone(props.get("centroidLat"))
            self.assertIsNotNone(props.get("centroidLong"))

    def test_constituency_coords_are_inside_uk_bbox(self):
        problems = []

        def check(pt):
            lon, lat = pt[0], pt[1]
            if not (UK_LON_MIN <= lon <= UK_LON_MAX and UK_LAT_MIN <= lat <= UK_LAT_MAX):
                problems.append((lon, lat))

        for feat in self.constituencies["features"]:
            _walk_coords(feat["geometry"]["coordinates"], check)
        self.assertEqual(problems, [])

    def test_outline_is_polygonal_and_in_bbox(self):
        geom = self.outline["features"][0]["geometry"]
        self.assertIn(geom["type"], ("Polygon", "MultiPolygon"))
        problems = []

        def check(pt):
            lon, lat = pt[0], pt[1]
            if not (UK_LON_MIN - 0.2 <= lon <= UK_LON_MAX + 0.2 and UK_LAT_MIN - 0.2 <= lat <= UK_LAT_MAX + 0.2):
                problems.append((lon, lat))

        _walk_coords(geom["coordinates"], check)
        self.assertEqual(problems, [])

    def test_size_budgets(self):
        self.assertLessEqual(os.path.getsize(CONSTITUENCIES), MAX_CONSTITUENCY_BYTES)
        self.assertLessEqual(os.path.getsize(OUTLINE), MAX_OUTLINE_BYTES)

    def test_generator_script_is_checked_in(self):
        self.assertTrue(
            os.path.exists(os.path.join(REPO_ROOT, "scripts", "build_globe_constituency_layer.py"))
        )


if __name__ == "__main__":
    unittest.main()
