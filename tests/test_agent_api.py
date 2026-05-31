import importlib


def _auth_header(token: str = "test-token"):
    return {"Authorization": f"Bearer {token}"}


def _client_with_token(token: str = "test-token"):
    appmod = importlib.import_module("app")
    appmod._AGENT_API_TOKEN = token
    return appmod.app.test_client()


def test_agent_health_auth():
    client = _client_with_token()
    r = client.get("/api/agent/health")
    assert r.status_code == 401
    r2 = client.get("/api/agent/health", headers=_auth_header())
    assert r2.status_code == 200
    payload = r2.get_json()
    assert payload["ok"] is True
    assert "data" in payload


def test_agent_search_mps():
    client = _client_with_token()
    r = client.get("/api/agent/search_mps?q=lam", headers=_auth_header())
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert "results" in data
    assert isinstance(data["results"], list)


def test_agent_map_payload_party():
    client = _client_with_token()
    r = client.get("/api/agent/map_payload?mode=party-split", headers=_auth_header())
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert data["mode"] == "party-split"
    assert isinstance(data["map_data"], dict)


def test_agent_map_payload_vote_default_division():
    client = _client_with_token()
    r = client.get("/api/agent/map_payload?mode=vote-split", headers=_auth_header())
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        data = r.get_json()["data"]
        assert data["mode"] == "vote-split"
        assert "map_data" in data


def test_agent_global_countries_and_country():
    client = _client_with_token()
    r = client.get("/api/agent/global/countries?status=green&limit=5", headers=_auth_header())
    assert r.status_code == 200
    countries = r.get_json()["data"]["countries"]
    assert isinstance(countries, list)
    if countries:
        iso2 = countries[0].get("iso2")
        r2 = client.get(f"/api/agent/global/country/{iso2}", headers=_auth_header())
        assert r2.status_code == 200
        assert r2.get_json()["data"]["country"]["iso2"].upper() == iso2.upper()


def test_agent_deeplink_generation():
    client = _client_with_token()
    r = client.get("/api/agent/deeplink?target=mp&member_id=206", headers=_auth_header())
    assert r.status_code == 200
    assert r.get_json()["data"]["path"] == "/mp/206"

    r2 = client.get("/api/agent/deeplink?target=source-lens&cc=GB&lang=en", headers=_auth_header())
    assert r2.status_code == 200
    assert r2.get_json()["data"]["path"].startswith("/source-lens?")
