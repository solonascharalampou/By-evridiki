"""Tests for customizer API and auth endpoints"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": "evridiki2025"})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["token"]

@pytest.fixture(scope="module")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

class TestCustomizerAPI:
    def test_get_customizer_returns_grouped(self):
        r = requests.get(f"{BASE_URL}/api/customizer")
        assert r.status_code == 200
        data = r.json()
        assert "sponges" in data
        assert "fillings" in data
        assert "frostings" in data
        assert "decos" in data

    def test_sponges_count(self):
        r = requests.get(f"{BASE_URL}/api/customizer")
        data = r.json()
        assert len(data["sponges"]) >= 14, f"Expected 14 sponges, got {len(data['sponges'])}"

    def test_fillings_count(self):
        r = requests.get(f"{BASE_URL}/api/customizer")
        data = r.json()
        assert len(data["fillings"]) >= 10, f"Expected 10 fillings, got {len(data['fillings'])}"

    def test_frostings_count(self):
        r = requests.get(f"{BASE_URL}/api/customizer")
        data = r.json()
        assert len(data["frostings"]) >= 9, f"Expected 9 frostings, got {len(data['frostings'])}"

    def test_decos_count(self):
        r = requests.get(f"{BASE_URL}/api/customizer")
        data = r.json()
        assert len(data["decos"]) >= 39, f"Expected 39 decos, got {len(data['decos'])}"

    def test_sponge_has_required_fields(self):
        r = requests.get(f"{BASE_URL}/api/customizer")
        data = r.json()
        sponge = data["sponges"][0]
        assert "id" in sponge
        assert "name_en" in sponge
        assert "name_el" in sponge
        assert "color" in sponge

    def test_deco_has_category(self):
        r = requests.get(f"{BASE_URL}/api/customizer")
        data = r.json()
        deco = data["decos"][0]
        assert "category" in deco

    def test_add_sponge_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/customizer", json={
            "type": "sponge", "name_en": "Test", "name_el": "Τεστ", "color": "#fff"
        })
        assert r.status_code == 401

    def test_add_and_delete_sponge(self, auth_headers):
        # Add
        r = requests.post(f"{BASE_URL}/api/customizer",
            json={"type": "sponge", "name_en": "TEST_Sponge", "name_el": "Τεστ Σπόντζ", "color": "#aabbcc"},
            headers=auth_headers)
        assert r.status_code == 200
        created = r.json()
        assert created["name_en"] == "TEST_Sponge"
        opt_id = created["id"]

        # Verify appears in GET
        r2 = requests.get(f"{BASE_URL}/api/customizer")
        sponge_ids = [s["id"] for s in r2.json()["sponges"]]
        assert opt_id in sponge_ids

        # Delete
        r3 = requests.delete(f"{BASE_URL}/api/customizer/{opt_id}", headers=auth_headers)
        assert r3.status_code == 200

        # Verify removed
        r4 = requests.get(f"{BASE_URL}/api/customizer")
        sponge_ids_after = [s["id"] for s in r4.json()["sponges"]]
        assert opt_id not in sponge_ids_after

    def test_add_deco_with_category(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/customizer",
            json={"type": "deco", "name_en": "TEST_Deco", "name_el": "Τεστ Ντέκο", "color": "#112233", "category": "fruit"},
            headers=auth_headers)
        assert r.status_code == 200
        created = r.json()
        assert created["category"] == "fruit"
        # Cleanup
        requests.delete(f"{BASE_URL}/api/customizer/{created['id']}", headers=auth_headers)

    def test_delete_nonexistent_returns_404(self, auth_headers):
        r = requests.delete(f"{BASE_URL}/api/customizer/nonexistent999", headers=auth_headers)
        assert r.status_code == 404
