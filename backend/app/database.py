import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any

MVP_USER_ID = "user"
MVP_USERNAME = "user"
DEFAULT_BOARD_ID = "board-default"

DEFAULT_COLUMNS = [
    {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"]},
    {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
    {"id": "col-progress", "title": "In Progress", "cardIds": ["card-4", "card-5"]},
    {"id": "col-review", "title": "Review", "cardIds": ["card-6"]},
    {"id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"]},
]

DEFAULT_CARDS = {
    "card-1": {
        "id": "card-1",
        "title": "Align roadmap themes",
        "details": "Draft quarterly themes with impact statements and metrics.",
    },
    "card-2": {
        "id": "card-2",
        "title": "Gather customer signals",
        "details": "Review support tags, sales notes, and churn feedback.",
    },
    "card-3": {
        "id": "card-3",
        "title": "Prototype analytics view",
        "details": "Sketch initial dashboard layout and key drill-downs.",
    },
    "card-4": {
        "id": "card-4",
        "title": "Refine status language",
        "details": "Standardize column labels and tone across the board.",
    },
    "card-5": {
        "id": "card-5",
        "title": "Design card layout",
        "details": "Add hierarchy and spacing for scanning dense lists.",
    },
    "card-6": {
        "id": "card-6",
        "title": "QA micro-interactions",
        "details": "Verify hover, focus, and loading states.",
    },
    "card-7": {
        "id": "card-7",
        "title": "Ship marketing page",
        "details": "Final copy approved and asset pack delivered.",
    },
    "card-8": {
        "id": "card-8",
        "title": "Close onboarding sprint",
        "details": "Document release notes and share internally.",
    },
}


class BoardNotFoundError(ValueError):
    pass


class BoardOperationError(ValueError):
    pass


def get_database_path() -> Path:
    configured_path = os.getenv("PM_DATABASE_PATH")
    if configured_path:
        return Path(configured_path)

    return Path.cwd() / "data" / "pm.sqlite"


def initialize_database(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with connect(path) as connection:
        create_schema(connection)
        seed_default_board(connection)


def connect(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY,
          username TEXT NOT NULL UNIQUE,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS boards (
          id TEXT PRIMARY KEY,
          user_id TEXT NOT NULL,
          title TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
          UNIQUE (user_id)
        );

        CREATE TABLE IF NOT EXISTS columns (
          id TEXT PRIMARY KEY,
          board_id TEXT NOT NULL,
          title TEXT NOT NULL,
          position INTEGER NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
          UNIQUE (board_id, position)
        );

        CREATE TABLE IF NOT EXISTS cards (
          id TEXT PRIMARY KEY,
          board_id TEXT NOT NULL,
          column_id TEXT NOT NULL,
          title TEXT NOT NULL,
          details TEXT NOT NULL DEFAULT '',
          position INTEGER NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
          FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE,
          UNIQUE (column_id, position)
        );
        """
    )


def seed_default_board(connection: sqlite3.Connection) -> None:
    connection.execute(
        "INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)",
        (MVP_USER_ID, MVP_USERNAME),
    )
    connection.execute(
        "INSERT OR IGNORE INTO boards (id, user_id, title) VALUES (?, ?, ?)",
        (DEFAULT_BOARD_ID, MVP_USER_ID, "Project Board"),
    )

    for position, column in enumerate(DEFAULT_COLUMNS):
        connection.execute(
            """
            INSERT OR IGNORE INTO columns (id, board_id, title, position)
            VALUES (?, ?, ?, ?)
            """,
            (column["id"], DEFAULT_BOARD_ID, column["title"], position),
        )

        for card_position, card_id in enumerate(column["cardIds"]):
            card = DEFAULT_CARDS[card_id]
            connection.execute(
                """
                INSERT OR IGNORE INTO cards
                    (id, board_id, column_id, title, details, position)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    card["id"],
                    DEFAULT_BOARD_ID,
                    column["id"],
                    card["title"],
                    card["details"],
                    card_position,
                ),
            )


class BoardRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def get_board(self, user_id: str = MVP_USER_ID) -> dict[str, Any]:
        with connect(self.db_path) as connection:
            board = _get_board_row(connection, user_id)
            columns = connection.execute(
                """
                SELECT id, title
                FROM columns
                WHERE board_id = ?
                ORDER BY position
                """,
                (board["id"],),
            ).fetchall()
            cards = connection.execute(
                """
                SELECT id, column_id, title, details
                FROM cards
                WHERE board_id = ?
                ORDER BY column_id, position
                """,
                (board["id"],),
            ).fetchall()

        cards_by_id = {
            card["id"]: {
                "id": card["id"],
                "title": card["title"],
                "details": card["details"],
            }
            for card in cards
        }
        card_ids_by_column: dict[str, list[str]] = {
            column["id"]: [] for column in columns
        }
        for card in cards:
            card_ids_by_column[card["column_id"]].append(card["id"])

        return {
            "id": board["id"],
            "userId": board["user_id"],
            "columns": [
                {
                    "id": column["id"],
                    "title": column["title"],
                    "cardIds": card_ids_by_column[column["id"]],
                }
                for column in columns
            ],
            "cards": cards_by_id,
        }

    def rename_column(self, column_id: str, title: str) -> dict[str, Any]:
        title = _clean_title(title)
        with connect(self.db_path) as connection:
            board = _get_board_row(connection, MVP_USER_ID)
            if not _column_exists(connection, board["id"], column_id):
                raise BoardOperationError("Column not found.")

            connection.execute(
                """
                UPDATE columns
                SET title = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND board_id = ?
                """,
                (title, column_id, board["id"]),
            )
            _touch_board(connection, board["id"])

        return self.get_board()

    def create_card(self, column_id: str, title: str, details: str = "") -> dict[str, Any]:
        title = _clean_title(title)
        details = details.strip()
        with connect(self.db_path) as connection:
            board = _get_board_row(connection, MVP_USER_ID)
            if not _column_exists(connection, board["id"], column_id):
                raise BoardOperationError("Column not found.")

            position = _next_card_position(connection, column_id)
            card_id = f"card-{uuid.uuid4().hex[:12]}"
            connection.execute(
                """
                INSERT INTO cards (id, board_id, column_id, title, details, position)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (card_id, board["id"], column_id, title, details, position),
            )
            _touch_board(connection, board["id"])

        return self.get_board()

    def edit_card(self, card_id: str, title: str, details: str = "") -> dict[str, Any]:
        title = _clean_title(title)
        details = details.strip()
        with connect(self.db_path) as connection:
            board = _get_board_row(connection, MVP_USER_ID)
            if not _card_exists(connection, board["id"], card_id):
                raise BoardOperationError("Card not found.")

            connection.execute(
                """
                UPDATE cards
                SET title = ?, details = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND board_id = ?
                """,
                (title, details, card_id, board["id"]),
            )
            _touch_board(connection, board["id"])

        return self.get_board()

    def delete_card(self, card_id: str) -> dict[str, Any]:
        with connect(self.db_path) as connection:
            board = _get_board_row(connection, MVP_USER_ID)
            card = _get_card_row(connection, board["id"], card_id)

            connection.execute(
                "DELETE FROM cards WHERE id = ? AND board_id = ?",
                (card_id, board["id"]),
            )
            _set_column_order(
                connection,
                card["column_id"],
                _get_card_ids(connection, card["column_id"]),
            )
            _touch_board(connection, board["id"])

        return self.get_board()

    def move_card(self, card_id: str, column_id: str, position: int) -> dict[str, Any]:
        if position < 0:
            raise BoardOperationError("Position must be greater than or equal to 0.")

        with connect(self.db_path) as connection:
            board = _get_board_row(connection, MVP_USER_ID)
            card = _get_card_row(connection, board["id"], card_id)
            if not _column_exists(connection, board["id"], column_id):
                raise BoardOperationError("Column not found.")

            source_column_id = card["column_id"]
            source_ids = [
                current_card_id
                for current_card_id in _get_card_ids(connection, source_column_id)
                if current_card_id != card_id
            ]

            if source_column_id == column_id:
                target_ids = source_ids
                target_ids.insert(min(position, len(target_ids)), card_id)
                _set_column_order(connection, column_id, target_ids)
            else:
                target_ids = _get_card_ids(connection, column_id)
                target_ids.insert(min(position, len(target_ids)), card_id)
                connection.execute(
                    """
                    UPDATE cards
                    SET column_id = ?, position = -1000000, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND board_id = ?
                    """,
                    (column_id, card_id, board["id"]),
                )
                _set_column_order(connection, source_column_id, source_ids)
                _set_column_order(connection, column_id, target_ids)

            _touch_board(connection, board["id"])

        return self.get_board()


def _get_board_row(connection: sqlite3.Connection, user_id: str) -> sqlite3.Row:
    board = connection.execute(
        "SELECT id, user_id FROM boards WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if board is None:
        raise BoardNotFoundError("Board not found.")
    return board


def _column_exists(connection: sqlite3.Connection, board_id: str, column_id: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM columns WHERE id = ? AND board_id = ?",
            (column_id, board_id),
        ).fetchone()
        is not None
    )


def _card_exists(connection: sqlite3.Connection, board_id: str, card_id: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM cards WHERE id = ? AND board_id = ?",
            (card_id, board_id),
        ).fetchone()
        is not None
    )


def _get_card_row(
    connection: sqlite3.Connection, board_id: str, card_id: str
) -> sqlite3.Row:
    card = connection.execute(
        "SELECT id, column_id FROM cards WHERE id = ? AND board_id = ?",
        (card_id, board_id),
    ).fetchone()
    if card is None:
        raise BoardOperationError("Card not found.")
    return card


def _get_card_ids(connection: sqlite3.Connection, column_id: str) -> list[str]:
    return [
        row["id"]
        for row in connection.execute(
            "SELECT id FROM cards WHERE column_id = ? ORDER BY position",
            (column_id,),
        ).fetchall()
    ]


def _next_card_position(connection: sqlite3.Connection, column_id: str) -> int:
    row = connection.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 AS next_position FROM cards WHERE column_id = ?",
        (column_id,),
    ).fetchone()
    return int(row["next_position"])


def _set_column_order(
    connection: sqlite3.Connection, column_id: str, card_ids: list[str]
) -> None:
    for index, card_id in enumerate(card_ids):
        connection.execute(
            "UPDATE cards SET position = ? WHERE id = ? AND column_id = ?",
            (-(index + 1000001), card_id, column_id),
        )
    for index, card_id in enumerate(card_ids):
        connection.execute(
            """
            UPDATE cards
            SET position = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND column_id = ?
            """,
            (index, card_id, column_id),
        )


def _touch_board(connection: sqlite3.Connection, board_id: str) -> None:
    connection.execute(
        "UPDATE boards SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (board_id,),
    )


def _clean_title(title: str) -> str:
    cleaned_title = title.strip()
    if not cleaned_title:
        raise BoardOperationError("Title cannot be empty.")
    return cleaned_title
