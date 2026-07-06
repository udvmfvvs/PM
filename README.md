# Project Management MVP

## Локальный запуск

Windows:

```powershell
.\scripts\start.ps1
```

macOS:

```sh
sh scripts/start-mac.sh
```

Linux:

```sh
sh scripts/start-linux.sh
```

Приложение будет доступно на `http://localhost:8000`.

Dummy credentials для MVP:

- username: `user`
- password: `password`

Проверка приложения:

- `http://localhost:8000/` отдает login screen, а после входа Kanban board.
- `http://localhost:8000/api/health` возвращает `{"status":"ok"}`.
- `http://localhost:8000/api/board` возвращает текущий board JSON.
- `POST http://localhost:8000/api/ai/connectivity-test` проверяет OpenRouter prompt `2+2`, если `OPENROUTER_API_KEY` задан в корневом `.env`.
- `POST http://localhost:8000/api/ai/chat` отправляет AI текущий board, message и history, затем возвращает assistant message и optional updated board.

SQLite database хранится в Docker volume `pm-data` по пути `/app/data/pm.sqlite`.
Изменения Kanban board сохраняются через backend API и переживают reload.
AI sidebar доступен на Kanban screen после входа и обновляет board без ручного reload, если backend возвращает updated board.

## Остановка

Windows:

```powershell
.\scripts\stop.ps1
```

macOS:

```sh
sh scripts/stop-mac.sh
```

Linux:

```sh
sh scripts/stop-linux.sh
```

## Backend tests

```sh
cd backend
uv sync
uv run pytest
```

## Frontend tests

```sh
cd frontend
npm run test:unit
npm run test:e2e
```
