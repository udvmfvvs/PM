import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.ai_board import (
    AIChatRequest,
    AIChatResponse,
    AIResponseValidationError,
    apply_ai_board_replacement,
    apply_ai_operations,
    build_ai_board_prompt,
    parse_ai_structured_response,
)
from app.ai_service import AIConfigurationError, AIServiceError, OpenRouterAIService
from app.database import (
    BoardNotFoundError,
    BoardOperationError,
    BoardRepository,
    get_database_path,
    initialize_database,
)


class RenameColumnRequest(BaseModel):
    title: str = Field(min_length=1)


class CreateCardRequest(BaseModel):
    columnId: str = Field(min_length=1)
    title: str = Field(min_length=1)
    details: str = ""


class EditCardRequest(BaseModel):
    title: str = Field(min_length=1)
    details: str = ""


class MoveCardRequest(BaseModel):
    columnId: str = Field(min_length=1)
    position: int = Field(ge=0)


class AIConnectivityResponse(BaseModel):
    prompt: str
    answer: str


def create_app(
    static_dir: str | Path | None = None,
    db_path: str | Path | None = None,
    ai_service: OpenRouterAIService | None = None,
) -> FastAPI:
    app = FastAPI(title="Project Management MVP")
    database_path = Path(db_path) if db_path is not None else get_database_path()
    initialize_database(database_path)
    repository = BoardRepository(database_path)
    configured_ai_service = ai_service or OpenRouterAIService()

    @app.get("/api/health")
    def read_health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/board")
    def read_board() -> dict[str, Any]:
        return _run_board_operation(repository.get_board)

    @app.patch("/api/board/columns/{column_id}")
    def rename_column(
        column_id: str,
        request: RenameColumnRequest,
    ) -> dict[str, Any]:
        return _run_board_operation(
            repository.rename_column,
            column_id,
            request.title,
        )

    @app.post("/api/board/cards", status_code=201)
    def create_card(request: CreateCardRequest) -> dict[str, Any]:
        return _run_board_operation(
            repository.create_card,
            request.columnId,
            request.title,
            request.details,
        )

    @app.patch("/api/board/cards/{card_id}")
    def edit_card(card_id: str, request: EditCardRequest) -> dict[str, Any]:
        return _run_board_operation(
            repository.edit_card,
            card_id,
            request.title,
            request.details,
        )

    @app.delete("/api/board/cards/{card_id}")
    def delete_card(card_id: str) -> dict[str, Any]:
        return _run_board_operation(repository.delete_card, card_id)

    @app.post("/api/board/cards/{card_id}/move")
    def move_card(card_id: str, request: MoveCardRequest) -> dict[str, Any]:
        return _run_board_operation(
            repository.move_card,
            card_id,
            request.columnId,
            request.position,
        )

    @app.post("/api/ai/connectivity-test")
    def test_ai_connectivity() -> AIConnectivityResponse:
        prompt = "2+2"
        try:
            answer = configured_ai_service.ask(prompt)
        except AIConfigurationError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except AIServiceError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error

        return AIConnectivityResponse(prompt=prompt, answer=answer)

    @app.post("/api/ai/chat")
    def chat_with_ai(request: AIChatRequest) -> AIChatResponse:
        current_board = _run_board_operation(repository.get_board)
        prompt = build_ai_board_prompt(current_board, request.message, request.history)
        try:
            raw_ai_response = configured_ai_service.ask(prompt)
            ai_response = parse_ai_structured_response(raw_ai_response)
        except AIConfigurationError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except AIServiceError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        except AIResponseValidationError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error

        updated_board: dict[str, Any] | None = None
        try:
            if ai_response.operations:
                updated_board = apply_ai_operations(repository, ai_response.operations)
            elif ai_response.board is not None:
                updated_board = apply_ai_board_replacement(
                    repository,
                    current_board,
                    ai_response.board,
                )
        except BoardOperationError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        return AIChatResponse(message=ai_response.message, board=updated_board)

    static_path = _resolve_static_dir(static_dir)
    if (static_path / "index.html").exists():
        app.mount("/", StaticFiles(directory=static_path, html=True), name="frontend")
        return app

    @app.get("/", response_class=HTMLResponse)
    def read_root() -> str:
        return """
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>Project Management MVP</title>
          </head>
          <body>
            <main>
              <h1>Project Management MVP</h1>
              <p>Hello from the FastAPI backend.</p>
            </main>
          </body>
        </html>
        """

    return app


def _resolve_static_dir(static_dir: str | Path | None) -> Path:
    if static_dir is not None:
        return Path(static_dir)

    configured_dir = os.getenv("FRONTEND_STATIC_DIR")
    if configured_dir:
        return Path(configured_dir)

    return Path(__file__).resolve().parent.parent / "static"


def _run_board_operation(operation, *args):
    try:
        return operation(*args)
    except BoardNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except BoardOperationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


app = create_app()
