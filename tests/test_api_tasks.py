from app import app


def test_api_requires_auth_redirect():
    client = app.test_client()
    response = client.get("/api/tasks")
    assert response.status_code in (301, 302, 401)
