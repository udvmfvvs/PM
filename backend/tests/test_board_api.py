from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(db_path=tmp_path / "pm.sqlite"))


def test_database_is_created_and_seeded(tmp_path: Path) -> None:
    db_path = tmp_path / "pm.sqlite"
    client = TestClient(create_app(db_path=db_path))

    response = client.get("/api/board")

    assert db_path.exists()
    assert response.status_code == 200
    board = response.json()
    assert board["id"] == "board-default"
    assert board["userId"] == "user"
    assert [column["id"] for column in board["columns"]] == [
        "col-backlog",
        "col-discovery",
        "col-progress",
        "col-review",
        "col-done",
    ]
    assert board["columns"][0]["cardIds"] == ["card-1", "card-2"]
    assert board["cards"]["card-1"]["title"] == "Align roadmap themes"


def test_renames_column(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.patch(
        "/api/board/columns/col-backlog",
        json={"title": "Ideas"},
    )

    assert response.status_code == 200
    assert response.json()["columns"][0]["title"] == "Ideas"


def test_rejects_empty_column_title(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.patch(
        "/api/board/columns/col-backlog",
        json={"title": "   "},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Title cannot be empty."


def test_creates_card_at_end_of_column(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/api/board/cards",
        json={
            "columnId": "col-backlog",
            "title": "New backend card",
            "details": "Created by API.",
        },
    )

    assert response.status_code == 201
    board = response.json()
    new_card_id = board["columns"][0]["cardIds"][-1]
    assert board["cards"][new_card_id] == {
        "id": new_card_id,
        "title": "New backend card",
        "details": "Created by API.",
    }


def test_edits_card(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.patch(
        "/api/board/cards/card-1",
        json={"title": "Updated title", "details": "Updated details."},
    )

    assert response.status_code == 200
    assert response.json()["cards"]["card-1"] == {
        "id": "card-1",
        "title": "Updated title",
        "details": "Updated details.",
    }


def test_deletes_card_and_preserves_order(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.delete("/api/board/cards/card-1")

    assert response.status_code == 200
    board = response.json()
    assert board["columns"][0]["cardIds"] == ["card-2"]
    assert "card-1" not in board["cards"]


def test_moves_card_between_columns(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/api/board/cards/card-2/move",
        json={"columnId": "col-review", "position": 1},
    )

    assert response.status_code == 200
    board = response.json()
    assert board["columns"][0]["cardIds"] == ["card-1"]
    assert board["columns"][3]["cardIds"] == ["card-6", "card-2"]


def test_moves_card_within_column(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/api/board/cards/card-2/move",
        json={"columnId": "col-backlog", "position": 0},
    )

    assert response.status_code == 200
    assert response.json()["columns"][0]["cardIds"] == ["card-2", "card-1"]


def test_returns_clear_error_for_missing_column(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/api/board/cards",
        json={"columnId": "missing", "title": "No column"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Column not found."
