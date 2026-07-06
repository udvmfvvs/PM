import json
from pathlib import Path
from urllib.request import Request

import pytest
from fastapi.testclient import TestClient

from app.ai_service import (
    OPENROUTER_MODEL,
    AIConfigurationError,
    OpenRouterAIService,
    build_openrouter_request,
    get_openrouter_api_key,
)
from app.main import create_app


def test_builds_openrouter_request() -> None:
    request = build_openrouter_request(
        api_key="test-key",
        model=OPENROUTER_MODEL,
        api_url="https://openrouter.example.test/chat",
        prompt="2+2",
    )

    payload = json.loads(request.data.decode("utf-8"))
    assert request.full_url == "https://openrouter.example.test/chat"
    assert request.method == "POST"
    assert request.headers["Authorization"] == "Bearer test-key"
    assert payload == {
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": "2+2"}],
    }


def test_reads_openrouter_api_key_from_root_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("OPENROUTER_API_KEY='local-test-key'\n", encoding="utf-8")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr("app.ai_service._env_candidates", lambda: [env_path])

    assert get_openrouter_api_key() == "local-test-key"


def test_missing_openrouter_api_key_has_clear_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr("app.ai_service._env_candidates", lambda: [])

    with pytest.raises(AIConfigurationError, match="OPENROUTER_API_KEY is not configured."):
        get_openrouter_api_key()


def test_ai_service_uses_mocked_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_requests: list[Request] = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {"choices": [{"message": {"content": "4"}}]},
            ).encode("utf-8")

    def fake_urlopen(request: Request, timeout: int):
        captured_requests.append(request)
        assert timeout == 30
        return FakeResponse()

    monkeypatch.setattr("app.ai_service.urlopen", fake_urlopen)

    service = OpenRouterAIService(api_key="test-key")

    assert service.ask("2+2") == "4"
    payload = json.loads(captured_requests[0].data.decode("utf-8"))
    assert payload["model"] == OPENROUTER_MODEL
    assert payload["messages"][0]["content"] == "2+2"


def test_ai_connectivity_endpoint_uses_prompt_2_plus_2(tmp_path: Path) -> None:
    class FakeAIService:
        def ask(self, prompt: str) -> str:
            assert prompt == "2+2"
            return "4"

    client = TestClient(create_app(db_path=tmp_path / "pm.sqlite", ai_service=FakeAIService()))

    response = client.post("/api/ai/connectivity-test")

    assert response.status_code == 200
    assert response.json() == {"prompt": "2+2", "answer": "4"}
