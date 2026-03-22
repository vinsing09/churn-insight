def test_health_check(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_protected_routes_require_auth(test_client):
    """All data routes must return 401 when no token is provided."""
    routes = [
        ("GET", "/api/v1/integrations"),
        ("GET", "/api/v1/analysis/status"),
        ("GET", "/api/v1/analysis/runs"),
        ("GET", "/api/v1/themes"),
        ("GET", "/api/v1/briefs"),
        ("GET", "/api/v1/dashboard/summary"),
        ("GET", "/api/v1/account"),
        ("GET", "/api/v1/auth/me"),
    ]
    for method, path in routes:
        response = test_client.request(method, path)
        assert response.status_code == 401, f"{method} {path} should be 401, got {response.status_code}"
