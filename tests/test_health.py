def test_health_check(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_placeholder_routes(test_client):
    """Verify all placeholder routes return 200 with not-implemented message."""
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
        assert response.status_code == 200, f"{method} {path} returned {response.status_code}"
        assert response.json() == {"message": "not implemented"}, f"{method} {path}"
