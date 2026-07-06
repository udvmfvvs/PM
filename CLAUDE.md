# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Проект

MVP приложения single-board Kanban для управления проектами: NextJS frontend, отдаваемый статически через Python FastAPI backend, упакованный в один Docker container с SQLite persistence и AI chat sidebar (через OpenRouter), который может изменять board.

Ограничения MVP scope (сохраняйте их): hardcoded login `user`/`password`, ровно один board на пользователя, пять фиксированных columns, которые можно только переименовывать (никогда не добавлять/удалять/переупорядочивать). Не over-engineer и не добавляйте features сверх MVP. Никогда не используйте emojis в коде или документации. Исправляйте root cause, доказанный фактами, а не догадками.

Документы планирования/дизайна находятся в `docs/` (`PLAN.md`, `DATABASE.md`). Файлы `AGENTS.md` в корне и в `backend/`, `frontend/`, `scripts/` написаны на русском и остаются авторитетными заметками для каждой директории.

> Примечание о языке: документация проекта (`AGENTS.md`, `docs/PLAN.md`, `docs/DATABASE.md`, `README.md`) написана на русском языке. Этот файл `CLAUDE.md` также на русском; технические термины (Kanban, board, column, card, endpoint и т.п.) намеренно оставлены без перевода для соответствия коду.

## Команды

Запуск полного приложения локально (Docker, отдается на `http://localhost:8000`):
- Windows: `.\scripts\start.ps1` / `.\scripts\stop.ps1`
- macOS: `sh scripts/start-mac.sh` / `sh scripts/stop-mac.sh`
- Linux: `sh scripts/start-linux.sh` / `sh scripts/stop-linux.sh`

Backend (`cd backend`):
- `uv sync` — установить зависимости
- `uv run fastapi run app/main.py --host 0.0.0.0 --port 8000` — запустить
- `uv run pytest` — все тесты; один тест: `uv run pytest tests/test_board_api.py::<test_name>`

Frontend (`cd frontend`):
- `npm run test:unit` — Vitest (один файл: `npx vitest run src/lib/kanban.test.ts`)
- `npm run test:e2e` — Playwright
- `npm run test:all` — unit + e2e
- `npm run lint` — ESLint
- `npm run build` — static export в `out/`

## Архитектура

**Развертывание в одном container.** `Dockerfile` многоэтапный: собирает NextJS static export (`next.config.ts` задает `output: "export"`), копирует `frontend/out` в backend image как `static/`, затем запускает FastAPI. В `app/main.py`, если `static/index.html` существует, FastAPI монтирует его на `/`; иначе отдает fallback hello-страницу. Именно поэтому все API routes имеют namespace под `/api` — они не должны конфликтовать со static mount на `/`.

**Формат данных board — это контракт**, общий для backend, frontend и AI. Board — это `{id, userId, columns: [{id, title, cardIds: []}], cards: {cardId: {id, title, details}}}`. Порядок columns и порядок cards внутри каждого column — это явные массивы. Этот точный формат определен в `backend/app/database.py` (сборка запросов) и продублирован в `frontend/src/lib/kanban.ts` (тип `BoardData`). Держите их синхронизированными.

**Слои backend** (`backend/app/`):
- `database.py` — SQLite schema, `initialize_database` (идемпотентное создание + seed default board) и `BoardRepository` — единственное место, которое читает/пишет в DB. Каждый метод mutation возвращает полностью пересобранный board. Порядок cards использует целочисленный `position` с constraint `UNIQUE(column_id, position)`; переупорядочивание сначала пишет отрицательные временные positions, чтобы избежать коллизий unique.
- `ai_service.py` — `OpenRouterAIService.ask(prompt)`; делает POST в OpenRouter (`openai/gpt-oss-120b`), используя только stdlib `urllib`. Загружает `OPENROUTER_API_KEY` из `.env` в корне проекта. Отсутствующий ключ вызывает `AIConfigurationError` (отдается как HTTP 503).
- `ai_board.py` — строит AI prompt (board JSON + message + history), парсит/валидирует structured AI response и применяет его. AI возвращает ЛИБО `operations` (rename_column/create_card/edit_card/delete_card/move_card), ЛИБО полную замену `board`, но никогда оба сразу. Оба пути идут через те же методы `BoardRepository`, что и REST API, поэтому AI-правки подчиняются той же валидации и не могут повредить board (например, replacement не может добавлять/удалять/переупорядочивать columns).
- `main.py` — фабрика `create_app()` связывает repository + AI service и определяет все routes. Ошибки маппятся на HTTP codes через `_run_board_operation` (`BoardNotFoundError`→404, `BoardOperationError`→400).

**API routes:** `GET /api/health`, `GET /api/board`, `PATCH /api/board/columns/{id}`, `POST /api/board/cards`, `PATCH|DELETE /api/board/cards/{id}`, `POST /api/board/cards/{id}/move`, `POST /api/ai/connectivity-test`, `POST /api/ai/chat`.

**Frontend** (`frontend/src/`): `page.tsx` → `AuthGate` (dummy login, session в `localStorage`) → `KanbanBoard`. Весь HTTP изолирован в `lib/api.ts` (`boardApi`, `aiApi`) — не разбрасывайте `fetch` calls по components. `KanbanBoard` хранит состояние board в React, и после каждой успешной mutation заменяет состояние на board, возвращенный backend (сервер — источник истины). Drag-and-drop использует `@dnd-kit`; `getMoveTarget` транслирует drop в вызов `moveCard(cardId, columnId, position)`. `AIChatSidebar` хранит session chat history и, когда `/api/ai/chat` возвращает обновленный board, передает его наверх через `onBoardUpdate`, чтобы UI обновился без reload.

## Конфигурация

- `PM_DATABASE_PATH` — путь к SQLite (по умолчанию `data/pm.sqlite` относительно cwd; `/app/data/pm.sqlite` в Docker, на volume `pm-data`).
- `FRONTEND_STATIC_DIR` — переопределяет директорию static frontend.
- `OPENROUTER_API_KEY` — читается из корневого `.env`; требуется для AI endpoints. Тесты внедряют mock AI service и никогда не нуждаются в реальном ключе.
