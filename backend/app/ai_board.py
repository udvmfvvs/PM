import json
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from app.database import BoardOperationError, BoardRepository


class AIResponseValidationError(ValueError):
    pass


class AIChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[AIChatMessage] = Field(default_factory=list)


class AIUpdateOperation(BaseModel):
    type: Literal["rename_column", "create_card", "edit_card", "delete_card", "move_card"]
    columnId: str | None = None
    cardId: str | None = None
    title: str | None = None
    details: str | None = None
    position: int | None = None


class AIStructuredResponse(BaseModel):
    message: str = Field(min_length=1)
    operations: list[AIUpdateOperation] = Field(default_factory=list)
    board: dict[str, Any] | None = None


class AIChatResponse(BaseModel):
    message: str
    board: dict[str, Any] | None = None


def build_ai_board_prompt(
    board: dict[str, Any],
    user_message: str,
    history: list[AIChatMessage],
) -> str:
    payload = {
        "instructions": (
            "You are an assistant for a Kanban project board. "
            "Return only valid JSON. Do not wrap it in Markdown. "
            "The JSON schema is: "
            '{"message":"text for the user","operations":[{"type":"create_card","columnId":"col-backlog","title":"Task","details":"Notes"}]}. '
            "operations is optional and can include rename_column, create_card, edit_card, delete_card, move_card. "
            "Use columnId, cardId, title, details, and position fields as needed. "
            "If replacing the whole board is simpler, return board with the same board JSON shape instead of operations."
        ),
        "currentBoard": board,
        "conversationHistory": [message.model_dump() for message in history],
        "userMessage": user_message,
    }
    return json.dumps(payload, ensure_ascii=False)


def parse_ai_structured_response(raw_response: str) -> AIStructuredResponse:
    try:
        payload = json.loads(_strip_json_fence(raw_response))
    except json.JSONDecodeError as error:
        raise AIResponseValidationError("AI response was not valid JSON.") from error

    try:
        response = AIStructuredResponse.model_validate(payload)
    except ValidationError as error:
        raise AIResponseValidationError("AI response did not match the expected schema.") from error

    if response.operations and response.board is not None:
        raise AIResponseValidationError("AI response cannot include both operations and board.")
    return response


def apply_ai_operations(
    repository: BoardRepository,
    operations: list[AIUpdateOperation],
) -> dict[str, Any]:
    board: dict[str, Any] | None = None
    for operation in operations:
        board = _apply_ai_operation(repository, operation)

    return board if board is not None else repository.get_board()


def apply_ai_board_replacement(
    repository: BoardRepository,
    current_board: dict[str, Any],
    replacement_board: dict[str, Any],
) -> dict[str, Any]:
    _validate_board_replacement(current_board, replacement_board)

    board = current_board
    current_column_ids = [column["id"] for column in current_board["columns"]]
    replacement_columns = {column["id"]: column for column in replacement_board["columns"]}

    for current_column in current_board["columns"]:
        replacement_column = replacement_columns[current_column["id"]]
        if current_column["title"] != replacement_column["title"]:
            board = repository.rename_column(current_column["id"], replacement_column["title"])

    replacement_card_ids = set(replacement_board["cards"].keys())
    for card_id in list(current_board["cards"].keys()):
        if card_id not in replacement_card_ids:
            board = repository.delete_card(card_id)

    board = repository.get_board()
    for column_id in current_column_ids:
        for position, card_id in enumerate(replacement_columns[column_id]["cardIds"]):
            replacement_card = replacement_board["cards"][card_id]
            if card_id not in board["cards"]:
                board = repository.create_card(
                    column_id,
                    replacement_card["title"],
                    replacement_card.get("details", ""),
                )
                created_card_id = board["columns"][
                    current_column_ids.index(column_id)
                ]["cardIds"][-1]
                board = repository.move_card(created_card_id, column_id, position)
                continue

            current_card = board["cards"][card_id]
            if (
                current_card["title"] != replacement_card["title"]
                or current_card["details"] != replacement_card.get("details", "")
            ):
                board = repository.edit_card(
                    card_id,
                    replacement_card["title"],
                    replacement_card.get("details", ""),
                )
            board = repository.move_card(card_id, column_id, position)

    return board


def _apply_ai_operation(
    repository: BoardRepository,
    operation: AIUpdateOperation,
) -> dict[str, Any]:
    if operation.type == "rename_column":
        return repository.rename_column(
            _required(operation.columnId, "columnId"),
            _required(operation.title, "title"),
        )
    if operation.type == "create_card":
        return repository.create_card(
            _required(operation.columnId, "columnId"),
            _required(operation.title, "title"),
            operation.details or "",
        )
    if operation.type == "edit_card":
        return repository.edit_card(
            _required(operation.cardId, "cardId"),
            _required(operation.title, "title"),
            operation.details or "",
        )
    if operation.type == "delete_card":
        return repository.delete_card(_required(operation.cardId, "cardId"))
    if operation.type == "move_card":
        position = operation.position
        if position is None:
            raise BoardOperationError("AI operation is missing position.")
        return repository.move_card(
            _required(operation.cardId, "cardId"),
            _required(operation.columnId, "columnId"),
            position,
        )

    raise BoardOperationError("Unsupported AI operation.")


def _required(value: str | None, field_name: str) -> str:
    if value is None:
        raise BoardOperationError(f"AI operation is missing {field_name}.")
    return value


def _validate_board_replacement(
    current_board: dict[str, Any],
    replacement_board: dict[str, Any],
) -> None:
    if replacement_board.get("id") != current_board.get("id"):
        raise BoardOperationError("AI board replacement has invalid board id.")
    if replacement_board.get("userId") != current_board.get("userId"):
        raise BoardOperationError("AI board replacement has invalid user id.")

    columns = replacement_board.get("columns")
    cards = replacement_board.get("cards")
    if not isinstance(columns, list) or not isinstance(cards, dict):
        raise BoardOperationError("AI board replacement has invalid shape.")

    current_column_ids = [column["id"] for column in current_board["columns"]]
    replacement_column_ids = [column.get("id") for column in columns]
    if replacement_column_ids != current_column_ids:
        raise BoardOperationError("AI board replacement cannot add, remove, or reorder columns.")

    listed_card_ids: list[str] = []
    for column in columns:
        if not isinstance(column.get("title"), str):
            raise BoardOperationError("AI board replacement has invalid column title.")
        card_ids = column.get("cardIds")
        if not isinstance(card_ids, list) or not all(isinstance(card_id, str) for card_id in card_ids):
            raise BoardOperationError("AI board replacement has invalid card order.")
        listed_card_ids.extend(card_ids)

    if len(listed_card_ids) != len(set(listed_card_ids)):
        raise BoardOperationError("AI board replacement contains duplicate card ids.")
    if set(listed_card_ids) != set(cards.keys()):
        raise BoardOperationError("AI board replacement cardIds do not match cards.")

    for card_id, card in cards.items():
        if not isinstance(card, dict) or card.get("id") != card_id:
            raise BoardOperationError("AI board replacement has invalid card id.")
        if not isinstance(card.get("title"), str) or not isinstance(card.get("details", ""), str):
            raise BoardOperationError("AI board replacement has invalid card content.")


def _strip_json_fence(raw_response: str) -> str:
    stripped_response = raw_response.strip()
    if not stripped_response.startswith("```"):
        return stripped_response

    lines = stripped_response.splitlines()
    if len(lines) >= 3 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped_response
