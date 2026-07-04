from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app, create_app


client = TestClient(app)


def test_root_serves_hello_page() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Hello from the FastAPI backend." in response.text


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_serves_static_frontend_when_available(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        "<!doctype html><h1>Kanban Studio</h1>",
        encoding="utf-8",
    )
    static_client = TestClient(create_app(static_dir=tmp_path))

    root_response = static_client.get("/")
    health_response = static_client.get("/api/health")

    assert root_response.status_code == 200
    assert "Kanban Studio" in root_response.text
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
