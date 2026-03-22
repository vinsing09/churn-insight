"""Integration tests for auth, account, dashboard, themes, and briefs routes."""
import uuid

import pytest
from fastapi.testclient import TestClient

EMAIL = "test@example.com"
PASSWORD = "supersecret123"


def _register_and_login(client: TestClient) -> str:
    """Register a new account and return a bearer token."""
    client.post("/api/v1/auth/register", json={"email": EMAIL, "password": PASSWORD})
    resp = client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_register(test_client: TestClient):
    resp = test_client.post("/api/v1/auth/register", json={"email": EMAIL, "password": PASSWORD})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == EMAIL
    assert data["plan"] == "trial"
    assert "id" in data


def test_register_duplicate_email(test_client: TestClient):
    test_client.post("/api/v1/auth/register", json={"email": EMAIL, "password": PASSWORD})
    resp = test_client.post("/api/v1/auth/register", json={"email": EMAIL, "password": PASSWORD})
    assert resp.status_code == 400


def test_login_success(test_client: TestClient):
    test_client.post("/api/v1/auth/register", json={"email": EMAIL, "password": PASSWORD})
    resp = test_client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(test_client: TestClient):
    test_client.post("/api/v1/auth/register", json={"email": EMAIL, "password": PASSWORD})
    resp = test_client.post("/api/v1/auth/login", json={"email": EMAIL, "password": "wrong"})
    assert resp.status_code == 401


def test_me(test_client: TestClient):
    token = _register_and_login(test_client)
    resp = test_client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["email"] == EMAIL


def test_me_no_token(test_client: TestClient):
    resp = test_client.get("/api/v1/auth/me")
    assert resp.status_code == 401


# ── Account ───────────────────────────────────────────────────────────────────

def test_get_account(test_client: TestClient):
    token = _register_and_login(test_client)
    resp = test_client.get("/api/v1/account", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["email"] == EMAIL


def test_update_ad_copy(test_client: TestClient):
    token = _register_and_login(test_client)
    resp = test_client.put(
        "/api/v1/account/ad-copy",
        json={"ad_copy": "Try our platform free for 14 days"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["ad_copy"] == "Try our platform free for 14 days"


# ── Dashboard ─────────────────────────────────────────────────────────────────

def test_dashboard_summary_empty(test_client: TestClient):
    token = _register_and_login(test_client)
    resp = test_client.get("/api/v1/dashboard/summary", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_responses"] == 0
    assert data["total_themes"] == 0
    assert data["latest_run"] is None


# ── Themes ────────────────────────────────────────────────────────────────────

def test_list_themes_empty(test_client: TestClient):
    token = _register_and_login(test_client)
    resp = test_client.get("/api/v1/themes", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_nonexistent_theme(test_client: TestClient):
    token = _register_and_login(test_client)
    resp = test_client.get(f"/api/v1/themes/{uuid.uuid4()}", headers=auth_headers(token))
    assert resp.status_code == 404


# ── Briefs ────────────────────────────────────────────────────────────────────

def test_list_briefs_empty(test_client: TestClient):
    token = _register_and_login(test_client)
    resp = test_client.get("/api/v1/briefs", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_generate_brief_unknown_theme(test_client: TestClient):
    token = _register_and_login(test_client)
    resp = test_client.post(
        "/api/v1/briefs/generate",
        json={"theme_id": str(uuid.uuid4())},
        headers=auth_headers(token),
    )
    assert resp.status_code == 404


# ── Integrations ──────────────────────────────────────────────────────────────

def test_list_integrations_empty(test_client: TestClient):
    token = _register_and_login(test_client)
    resp = test_client.get("/api/v1/integrations", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []


# ── Analysis ──────────────────────────────────────────────────────────────────

def test_analysis_status_no_runs(test_client: TestClient):
    token = _register_and_login(test_client)
    resp = test_client.get("/api/v1/analysis/status", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() is None


def test_list_runs_empty(test_client: TestClient):
    token = _register_and_login(test_client)
    resp = test_client.get("/api/v1/analysis/runs", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []
