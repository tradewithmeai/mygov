"""Tests for the site-wide _inject_seo_head after_request hook.

It adds shared SEO tags (meta description, canonical, Open Graph, Twitter card)
right after the first <head> on HTML pages, mirroring the feedback/skip-link
injectors: idempotent, HTML-only, skips /api /static and the /map/relay iframe,
and fails closed. Page-specific tags (<title>, JSON-LD) stay in the templates.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as appmod


def _client():
    return appmod.app.test_client()


def test_seo_tags_injected_on_html_page():
    body = _client().get("/source-lens").get_data(as_text=True)
    assert 'property="og:site_name"' in body
    assert 'name="twitter:card"' in body
    assert 'name="description"' in body
    assert 'rel="canonical"' in body


def test_canonical_and_og_url_use_the_request_path():
    body = _client().get("/source-lens").get_data(as_text=True)
    assert 'href="https://yourgov.solvx.uk/source-lens"' in body   # canonical
    assert 'content="https://yourgov.solvx.uk/source-lens"' in body  # og:url


def test_not_injected_twice():
    body = _client().get("/source-lens").get_data(as_text=True)
    assert body.count('property="og:site_name"') == 1


def test_map_relay_iframe_is_excluded():
    # The embeddable map iframe must not carry page SEO tags.
    body = _client().get("/map/relay").get_data(as_text=True)
    assert 'property="og:site_name"' not in body


def test_api_and_static_paths_are_skipped():
    # A JSON API response must be untouched (and is not text/html anyway).
    r = _client().get("/api/lens/source-divisions?limit=1")
    assert 'og:site_name' not in r.get_data(as_text=True)


def test_entry_shell_has_keyword_title_and_json_ld():
    body = _client().get("/source-lens").get_data(as_text=True)
    assert "<title>YourGov" in body and "UK Constituency Map" in body
    assert 'application/ld+json' in body and '"WebApplication"' in body
