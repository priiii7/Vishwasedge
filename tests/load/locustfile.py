"""Load test: 100 concurrent users hitting the query endpoint.

Not executed as part of this build (needs a live server) — run manually:
    locust -f tests/load/locustfile.py --host http://localhost:8000
"""

from locust import HttpUser, between, task


class VishwasEdgeUser(HttpUser):
    wait_time = between(1, 3)
    token: str | None = None

    def on_start(self) -> None:
        response = self.client.post(
            "/api/v1/auth/login", json={"username": "operator", "password": "changeme123"}
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    @task(3)
    def ask_query(self) -> None:
        if not self.token:
            return
        self.client.post(
            "/api/v1/query",
            json={
                "query": "What is the safe operating pressure for well W-123?",
                "options": {"stream": False, "include_explanation": True, "max_docs": 5},
            },
            headers={"Authorization": f"Bearer {self.token}"},
        )

    @task(1)
    def check_health(self) -> None:
        self.client.get("/health")
