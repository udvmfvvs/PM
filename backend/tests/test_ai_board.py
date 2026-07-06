import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ai_board import AIResponseValidationError, parse_ai_structured_response
from app.main import create_app


def test_parses_valid_structured_ai_output() -> None:
    response = parse_ai_structured_response(
        json.dumps(
            {
                "message": "Created a card.",
                "operations": [
                    {
                        "type": "create_card",
                        "columnId": "col-backlog",
                        "title": "Write release notes",
                        "details": "Summarize the shipped scope.",
                    }
                ],
            }
        )
    )

    assert response.message == "Created a card."
    assert response.operations[0].type == "create_card"
    assert response.operations[0].title == "Write release notes"


def test_rejects_malformed_ai_output() -> None:
    with pytest.raises(AIResponseValidationError, match="AI response was not valid JSON."):
        parse_ai_structured_response("not json")


def test_ai_chat_endpoint_applies_mocked_board_update(tmp_path: Path) -> None:
    class FakeAIService:
        def ask(self, prompt: str) -> str:
            prompt_payload = json.loads(prompt)
            assert prompt_payload["currentBoard"]["id"] == "board-default"
            assert prompt_payload["userMessage"] == "Create a launch prep card"
            return json.dumps(
                {
                    "message": "Added the launch prep card.",
                    "operations": [
                        {
                            "type": "create_card",
                            "columnId": "col-backlog",
                            "title": "Launch prep",
                            "details": "Confirm checklist before release.",
                        }
                    ],
                }
            )

    client = TestClient(create_app(db_path=tmp_path / "pm.sqlite", ai_service=FakeAIService()))

    response = client.post(
        "/api/ai/chat",
        json={
            "message": "Create a launch prep card",
            "history": [{"role": "user", "content": "Use the backlog for new tasks."}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Added the launch prep card."
    backlog_card_ids = body["board"]["columns"][0]["cardIds"]
    new_card_id = backlog_card_ids[-1]
    assert body["board"]["cards"][new_card_id]["title"] == "Launch prep"

    persisted_board = client.get("/api/board").json()
    assert persisted_board["cards"][new_card_id]["title"] == "Launch prep"


def test_ai_chat_endpoint_returns_chat_only_response(tmp_path: Path) -> None:
    class FakeAIService:
        def ask(self, prompt: str) -> str:
            return json.dumps({"message": "Nothing needs to change right now."})

    client = TestClient(create_app(db_path=tmp_path / "pm.sqlite", ai_service=FakeAIService()))

    response = client.post("/api/ai/chat", json={"message": "What should I do next?"})

    assert response.status_code == 200
    assert response.json() == {
        "message": "Nothing needs to change right now.",
        "board": None,
    }


def test_ai_chat_endpoint_applies_board_replacement(tmp_path: Path) -> None:
    class FakeAIService:
        def ask(self, prompt: str) -> str:
            board = json.loads(prompt)["currentBoard"]
            board["columns"][0]["title"] = "Ideas"
            board["columns"][0]["cardIds"].remove("card-1")
            board["columns"][3]["cardIds"].insert(0, "card-1")
            board["cards"]["card-1"]["title"] = "Updated by AI"
            return json.dumps(
                {
                    "message": "Updated the board.",
                    "board": board,
                }
            )

    client = TestClient(create_app(db_path=tmp_path / "pm.sqlite", ai_service=FakeAIService()))

    response = client.post("/api/ai/chat", json={"message": "Update the board"})

    assert response.status_code == 200
    board = response.json()["board"]
    assert board["columns"][0]["title"] == "Ideas"
    assert board["columns"][0]["cardIds"] == ["card-2"]
    assert board["columns"][3]["cardIds"][0] == "card-1"
    assert board["cards"]["card-1"]["title"] == "Updated by AI"


def test_ai_chat_endpoint_rejects_invalid_board_update(tmp_path: Path) -> None:
    class FakeAIService:
        def ask(self, prompt: str) -> str:
            return json.dumps(
                {
                    "message": "I tried to move it.",
                    "operations": [
                        {
                            "type": "move_card",
                            "cardId": "card-1",
                            "columnId": "missing-column",
                            "position": 0,
                        }
                    ],
                }
            )

    client = TestClient(create_app(db_path=tmp_path / "pm.sqlite", ai_service=FakeAIService()))

    response = client.post("/api/ai/chat", json={"message": "Move card one"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Column not found."
