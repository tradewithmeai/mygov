import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


class AbMapRouteTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    # ── /ab_map ──────────────────────────────────────────────────────

    def test_ab_map_default_returns_200(self):
        r = self.client.get("/ab_map")
        self.assertEqual(r.status_code, 200)

    def test_ab_map_default_is_variant_a(self):
        r = self.client.get("/ab_map")
        body = r.get_data(as_text=True)
        self.assertIn("Variant A", body)
        self.assertIn('src="/map"', body)

    def test_ab_map_variant_a_param(self):
        r = self.client.get("/ab_map?variant=a")
        self.assertEqual(r.status_code, 200)
        body = r.get_data(as_text=True)
        self.assertIn("Variant A", body)
        self.assertIn('src="/map"', body)
        self.assertNotIn('src="/map/pro"', body)

    def test_ab_map_variant_b_param(self):
        r = self.client.get("/ab_map?variant=b")
        self.assertEqual(r.status_code, 200)
        body = r.get_data(as_text=True)
        self.assertIn("Variant B", body)
        self.assertIn('src="/map/pro"', body)
        self.assertNotIn('src="/map"', body)

    def test_ab_map_invalid_variant_falls_back_to_a(self):
        r = self.client.get("/ab_map?variant=z")
        self.assertEqual(r.status_code, 200)
        body = r.get_data(as_text=True)
        self.assertIn("Variant A", body)

    def test_ab_map_contains_source_lens_link(self):
        r = self.client.get("/ab_map")
        body = r.get_data(as_text=True)
        self.assertIn("/source-lens", body)

    def test_ab_map_contains_telemetry_event(self):
        r = self.client.get("/ab_map?variant=b")
        body = r.get_data(as_text=True)
        self.assertIn("map_ab_variant_viewed", body)

    # ── /ab_map/<variant_id> sub-routes ──────────────────────────────

    def test_ab_map_slash_a_redirects(self):
        r = self.client.get("/ab_map/a")
        self.assertEqual(r.status_code, 302)
        self.assertIn("variant=a", r.headers["Location"])

    def test_ab_map_slash_b_redirects(self):
        r = self.client.get("/ab_map/b")
        self.assertEqual(r.status_code, 302)
        self.assertIn("variant=b", r.headers["Location"])

    def test_ab_map_slash_invalid_redirects_to_ab_map(self):
        r = self.client.get("/ab_map/xyz")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/ab_map", r.headers["Location"])

    # ── Sanity: existing routes still work ───────────────────────────

    def test_existing_map_route_intact(self):
        r = self.client.get("/map")
        self.assertEqual(r.status_code, 200)

    def test_existing_source_lens_route_intact(self):
        r = self.client.get("/source-lens")
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()
