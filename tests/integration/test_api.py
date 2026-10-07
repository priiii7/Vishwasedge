import io

from fastapi.testclient import TestClient

from backend.main import app


def _login(client: TestClient) -> str:
    response = client.post("/api/v1/auth/login", json={"username": "operator", "password": "changeme123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


def test_ready():
    with TestClient(app) as client:
        response = client.get("/ready")
        assert response.status_code == 200
        assert "checks" in response.json()


def test_metrics_endpoint():
    with TestClient(app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200


def test_login_and_me():
    with TestClient(app) as client:
        token = _login(client)
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        body = response.json()
        assert body["username"] == "operator"
        assert "query" in body["permissions"]


def test_login_rejects_bad_password():
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/login", json={"username": "operator", "password": "wrong"})
        assert response.status_code == 401


def test_query_requires_auth():
    with TestClient(app) as client:
        response = client.post("/api/v1/query", json={"query": "hello"})
        assert response.status_code == 401


def test_upload_then_query_end_to_end():
    with TestClient(app) as client:
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        doc_content = (
            b"The safe operating pressure for well W-123 is 4500 psi. "
            b"Exceeding 5000 psi triggers an automatic emergency shutdown of the wellhead valve."
        )
        files = {"file": ("safety_manual.txt", io.BytesIO(doc_content), "text/plain")}
        upload_response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data={"source": "safety_manual", "category": "operations"},
            headers=headers,
        )
        assert upload_response.status_code == 200
        job_id = upload_response.json()["job_id"]
        assert upload_response.json()["status"] == "completed"

        status_response = client.get(f"/api/v1/documents/status/{job_id}", headers=headers)
        assert status_response.status_code == 200
        assert status_response.json()["chunks_indexed"] >= 1

        query_response = client.post(
            "/api/v1/query",
            json={"query": "What is the safe operating pressure for well W-123?"},
            headers=headers,
        )
        assert query_response.status_code == 200
        body = query_response.json()
        assert "response" in body
        assert 0.0 <= body["confidence"] <= 1.0
        assert body["retrieval_metadata"]["num_docs_considered"] >= 1
        assert body["explanation"] is not None
        assert len(body["explanation"]["token_saliency"]) > 0
