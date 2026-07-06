# Заметки для агента по backend

## Текущий backend

Backend находится в этой директории и является Python FastAPI-приложением.

## Основные файлы

- `pyproject.toml` описывает uv-проект, runtime dependencies и dev dependencies.
- `app/main.py` создает FastAPI app, отдает static frontend на `/` при наличии `static/index.html`, fallback hello-страницу без сборки frontend и health endpoint на `/api/health`.
- `app/database.py` содержит SQLite schema, seed default board и repository для board read/write operations.
- `tests/test_main.py` содержит минимальные pytest-тесты для `/`, `/api/health` и static frontend serving.
- `tests/test_board_api.py` покрывает database initialization, default board creation и board mutation API.

## Команды

- `uv sync` устанавливает зависимости.
- `uv run fastapi run app/main.py --host 0.0.0.0 --port 8000` запускает backend.
- `uv run pytest` запускает backend-тесты.

## API routes

- `GET /api/board` возвращает current board.
- `PATCH /api/board/columns/{column_id}` переименовывает column.
- `POST /api/board/cards` создает card в target column.
- `PATCH /api/board/cards/{card_id}` редактирует card.
- `DELETE /api/board/cards/{card_id}` удаляет card.
- `POST /api/board/cards/{card_id}/move` перемещает card в column на заданную `position`.
- `POST /api/ai/connectivity-test` проверяет OpenRouter connectivity через prompt `2+2`.
- `POST /api/ai/chat` отправляет AI текущий board, user message и history, затем применяет valid board updates.

## Рекомендации

- Держать backend простым и ориентированным на MVP.
- API routes размещать под `/api`, чтобы не конфликтовать со статическим frontend на `/`.
- SQLite database path можно задать через `PM_DATABASE_PATH`; по умолчанию используется `data/pm.sqlite` относительно working directory.
- Не логировать secrets.
- Перед исправлением проблем сначала находить root cause.