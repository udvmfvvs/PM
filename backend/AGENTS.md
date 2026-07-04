# Заметки для агента по backend

## Текущий backend

Backend находится в этой директории и является Python FastAPI-приложением.

## Основные файлы

- `pyproject.toml` описывает uv-проект, runtime dependencies и dev dependencies.
- `app/main.py` создает FastAPI app, отдает static frontend на `/` при наличии `static/index.html`, fallback hello-страницу без сборки frontend и health endpoint на `/api/health`.
- `tests/test_main.py` содержит минимальные pytest-тесты для `/`, `/api/health` и static frontend serving.

## Команды

- `uv sync` устанавливает зависимости.
- `uv run fastapi run app/main.py --host 0.0.0.0 --port 8000` запускает backend.
- `uv run pytest` запускает backend-тесты.

## Рекомендации

- Держать backend простым и ориентированным на MVP.
- API routes размещать под `/api`, чтобы не конфликтовать со статическим frontend на `/`.
- Не логировать secrets.
- Перед исправлением проблем сначала находить root cause.