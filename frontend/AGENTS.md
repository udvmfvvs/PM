# Заметки для агента по frontend

## Текущее приложение

Эта директория содержит NextJS frontend для Project Management app.

Приложение написано на NextJS с React и TypeScript. Основной route рендерит auth gate из `src/app/page.tsx` через `src/components/AuthGate.tsx`, а после входа показывает `src/components/KanbanBoard.tsx`.

## Основные файлы

- `src/app/page.tsx` рендерит Kanban board на `/`.
- `src/app/layout.tsx` определяет app shell и metadata.
- `src/app/globals.css` содержит global styles, Tailwind setup и project color variables.
- `src/lib/api.ts` содержит небольшой API client для backend board routes.
- `src/lib/kanban.ts` содержит board types, initial demo data для тестов и card movement logic.
- `src/components/AuthGate.tsx` содержит MVP login/logout flow с dummy credentials `user` и `password`.
- `src/components/KanbanBoard.tsx` загружает board из backend API и обновляет локальное UI-состояние после successful mutations.
- `src/components/AIChatSidebar.tsx` хранит session conversation history, отправляет messages в backend AI endpoint и применяет updated board.
- `src/components/KanbanColumn.tsx` рендерит droppable column и редактируемый column title.
- `src/components/KanbanCard.tsx` рендерит sortable card, edit form и delete button.
- `src/components/NewCardForm.tsx` обрабатывает card creation через parent API mutation.
- `src/components/KanbanCardPreview.tsx` рендерит drag overlay preview.

## Текущее поведение

- Unauthenticated users видят login screen.
- Session state для MVP хранится в `localStorage`.
- После login board загружается из `/api/board`.
- Board state хранится в React state внутри `KanbanBoard` после backend responses.
- Columns можно переименовывать, изменения сохраняются через backend.
- Cards можно добавлять, редактировать и удалять через backend.
- Cards можно перемещать drag and drop через `@dnd-kit`.
- Изменения сохраняются в SQLite через backend API и переживают reload.
- AI sidebar отправляет chat messages в `/api/ai/chat`; если backend возвращает updated board, UI обновляется без reload.

## Тесты

Используйте существующий минимальный практичный набор тестов:

- `npm run test:unit` запускает Vitest tests.
- `npm run test:e2e` запускает Playwright tests.
- `npm run test:all` запускает unit tests и E2E tests.
- `npm run lint` запускает ESLint.
- `npm run build` создает static export в `out`.

Текущее покрытие тестами включает:

- `src/lib/kanban.test.ts` для card movement behavior.
- `src/components/KanbanBoard.test.tsx` для API-loaded rendering, renaming, adding, editing, deleting cards и AI chat refresh.
- `src/components/AuthGate.test.tsx` для успешного и неуспешного login.
- `tests/kanban.spec.ts` для Playwright smoke coverage login/logout, загрузки, добавления, редактирования, перемещения cards, persistence after reload и AI chat.

## Рекомендации по реализации

- Держать frontend простым и близким к существующему demo.
- Сохранять совместимость со static export, потому что FastAPI отдает собранный frontend из Docker image.
- Предпочитать небольшие components и обычный React state, если backend integration не требует другого подхода.
- Сохранять существующий visual style и project colors из корневого `AGENTS.md`.
- При подключении backend изолировать HTTP calls в небольшом API client, а не распределять `fetch` calls по components.
- Держать tests сфокусированными на MVP workflows: login, load board, mutate board, persistence и AI chat.
- Не добавлять unrelated UI settings, extra boards, real registration или model controls для MVP.
