# План проекта

Этот план разбивает MVP на небольшие этапы реализации. Каждый этап должен оставаться простым, по возможности использовать существующий frontend и включать минимальный практичный набор тестов для MVP.

## Часть 1: План

Цель: превратить общее направление проекта в рабочую документацию до начала реализации.

Чеклист:
- [x] Изучить корневой `AGENTS.md`.
- [x] Расширить этот план конкретными подшагами.
- [x] Добавить тесты и критерии успеха для каждой части реализации.
- [x] Создать `frontend/AGENTS.md` с описанием текущего frontend.
- [x] Получить подтверждение пользователя перед началом Части 2.

Тесты:
- Этап только документационный; автоматические тесты не требуются.

Критерии успеха:
- План достаточно подробный, чтобы агент мог выполнять его пошагово.
- Инструкции для frontend существуют и соответствуют текущему коду.
- Пользователь просмотрел и одобрил план.

## Часть 2: Каркас проекта

Цель: создать backend, Docker-настройку и локальные скрипты запуска/остановки с маленьким рабочим приложением.

Чеклист:
- [x] Создать `backend/` с минимальным FastAPI-приложением.
- [x] Добавить health endpoint, например `GET /api/health`.
- [x] Отдавать простой статический HTML с `/` до подключения сборки NextJS.
- [x] Добавить файлы Python-проекта с использованием `uv`.
- [x] Добавить Dockerfile и docker compose конфигурацию для локального запуска.
- [x] Добавить скрипты запуска и остановки для Windows, macOS и Linux в `scripts/`.
- [x] Кратко задокументировать базовый локальный запуск в README или docs.

Тесты:
- Unit-тест backend для health endpoint.
- Ручной smoke test через скрипт запуска:
  - `/` возвращает статическую hello-страницу;
  - `/api/health` возвращает успешный JSON-ответ.

Критерии успеха:
- Свежий checkout может запустить локальное приложение в Docker.
- Backend стартует без существующей базы данных.
- Скрипты запуска и остановки работают на целевых платформах.

## Часть 3: Подключение frontend

Цель: статически собрать существующий NextJS frontend и отдавать demo Kanban board из FastAPI на `/`.

Чеклист:
- [x] При необходимости настроить NextJS-приложение для static export.
- [x] Обновить Docker-сборку так, чтобы frontend собирался и копировался в backend image.
- [x] Настроить FastAPI для отдачи статического frontend на `/`.
- [x] Сохранить поведение frontend эквивалентным текущему demo.
- [x] Убедиться, что API routes остаются доступны под `/api`.

Тесты:
- Frontend unit-тесты через Vitest.
- Frontend Playwright smoke test для загрузки Kanban board.
- Backend или integration smoke test, подтверждающий, что `/` отдает собранное приложение.

Критерии успеха:
- Dockerized app показывает Kanban board на `/`.
- Существующее demo-поведение drag, rename, add и delete продолжает работать.
- Отдача статического frontend не блокирует API routes.

## Часть 4: Фейковый вход пользователя

Цель: требовать простой локальный sign in перед показом Kanban board.

Чеклист:
- [x] Добавить экран login для unauthenticated users.
- [x] Принимать только username `user` и password `password`.
- [x] Добавить logout.
- [x] Оставить authentication простой для MVP, без реальной регистрации пользователей.
- [x] Решить, где хранится session state для MVP, предпочитая самый простой локальный подход, если backend persistence не нужен.
- [x] Сохранить предположение на будущее, что база данных сможет поддерживать нескольких пользователей.

Тесты:
- Unit или component test для успешного login.
- Unit или component test для неуспешного login.
- E2E smoke test:
  - unauthenticated visit показывает login;
  - валидные credentials показывают board;
  - logout возвращает на login.

Критерии успеха:
- Пользователи не могут увидеть Kanban board до sign in.
- Валидные dummy credentials стабильно работают.
- Невалидные credentials показывают понятное состояние ошибки.

## Часть 5: Моделирование базы данных

Цель: спроектировать и задокументировать SQLite-backed модель данных Kanban, включая JSON-формат, используемый API и AI.

Чеклист:
- [x] Создать документ с дизайном базы данных в `docs/`.
- [x] Определить JSON-формат для board, columns, cards и порядка cards.
- [x] Определить SQLite tables, которые позже смогут поддерживать нескольких пользователей.
- [x] Для MVP оставить один board на signed-in user.
- [x] Решить, как создаются initial board data, если база данных пустая.
- [x] Задокументировать базовые constraints и update behavior.
- [x] Получить подтверждение пользователя перед реализацией базы данных.

Тесты:
- Этап только документационный; автоматические тесты не требуются.

Критерии успеха:
- JSON-формат board понятен и достаточно стабилен для frontend и AI.
- SQLite schema поддерживает MVP и оставляет место для нескольких пользователей.
- Пользователь одобрил подход к базе данных.

## Часть 6: Backend

Цель: добавить backend API routes для чтения и обновления Kanban board пользователя, с хранением в SQLite.

Чеклист:
- [x] Добавить инициализацию SQLite database при старте backend или при первом использовании.
- [x] Засеять default board, если для MVP user еще нет board.
- [x] Добавить API route для получения current board.
- [x] Добавить API routes или один update route для rename columns, create cards, edit cards, delete cards и move cards.
- [x] Валидировать request bodies простыми Pydantic models.
- [x] Держать API responses согласованными с задокументированным JSON-форматом board.
- [x] Добавить понятные error responses для невалидных board operations.

Тесты:
- Unit-тесты для database initialization и default board creation.
- API-тесты для получения board.
- API-тесты для каждой mutation, используемой frontend:
  - rename column;
  - create card;
  - edit card;
  - delete card;
  - move card.

Критерии успеха:
- База данных создается автоматически, если отсутствует.
- Backend tests покрывают основное read/write поведение board.
- API корректно сохраняет порядок cards и данные columns.

## Часть 7: Frontend + Backend

Цель: заменить in-memory состояние Kanban на persistence через backend API.

Чеклист:
- [x] Добавить небольшой frontend API client.
- [x] Загружать board из backend после login.
- [x] Сохранять column renames.
- [x] Добавить UI для редактирования cards, если он все еще отсутствует во frontend demo.
- [x] Сохранять card creation, edits, deletion и moves.
- [x] Показывать простые loading и error states.
- [x] Обновлять локальное UI-состояние после успешных backend updates.
- [x] Оставить UI простым и близким к существующему Kanban demo.

Тесты:
- Frontend unit/component test для рендера board data, загруженных из API, с использованием mocks.
- Frontend unit/component test минимум для одного mutation flow.
- Frontend unit/component test для редактирования card.
- E2E smoke test, подтверждающий persistence после page reload.
- Backend tests из Части 6 продолжают проходить.

Критерии успеха:
- Изменения board переживают page reload.
- Frontend больше не полагается на статические in-memory data для live board.
- Пользовательское поведение остается быстрым и понятным.

## Часть 8: AI connectivity

Цель: подтвердить, что backend может вызывать OpenRouter с настроенной моделью.

Чеклист:
- [x] Загружать `OPENROUTER_API_KEY` из `.env` в корне проекта.
- [x] Настроить OpenRouter с моделью `openai/gpt-oss-120b`.
- [x] Добавить минимальный backend AI service module.
- [x] Добавить временный или test-only connectivity path для простого prompt `2+2`.
- [x] Не логировать secrets.

Тесты:
- Unit-тест сборки AI service request с замоканной сетью.
- Ручной connectivity test, где OpenRouter возвращает ожидаемый ответ для `2+2`.

Критерии успеха:
- Backend может сделать реальный OpenRouter call локально, если API key присутствует.
- Автоматические тесты не требуют реального OpenRouter key.
- Отсутствующий API key приводит к понятной локальной configuration error.

## Часть 9: AI updates для board

Цель: отправлять AI JSON board, user message и conversation history, а затем обрабатывать structured output, который может обновить Kanban board.

Чеклист:
- [x] Определить schema для structured AI response.
- [ ] Включить:
  - [x] user-facing assistant response;
  - [x] optional Kanban update operation или full board replacement;
  - [x] достаточную validation, чтобы отклонять invalid board updates.
- [x] Отправлять current board JSON, user question и conversation history в OpenRouter.
- [x] Применять valid AI board updates через те же backend rules, которые используются обычными API operations.
- [x] Сохранять успешные AI updates.
- [x] Возвращать assistant message и updated board state, когда это применимо.

Тесты:
- Unit-тест для parsing valid structured AI output.
- Unit-тест для rejection malformed AI output.
- Backend API test с mocked AI response, который обновляет board.
- Backend API test с mocked AI response, который только отправляет chat reply.

Критерии успеха:
- AI responses не могут повредить persisted board.
- Backend может отличать chat-only responses от board-changing responses.
- Board updates от AI используют тот же JSON-формат, что и остальное приложение.

## Часть 10: AI sidebar widget

Цель: добавить AI chat sidebar в UI и обновлять Kanban, когда AI его меняет.

Чеклист:
- [x] Добавить sidebar chat component, который соответствует существующему visual style.
- [x] Хранить и отображать conversation history для текущей session.
- [x] Отправлять user messages в backend AI endpoint.
- [x] Показывать assistant responses.
- [x] Если AI возвращает updated board, автоматически refresh Kanban UI.
- [x] Добавить простые loading и error states для chat.
- [x] Держать sidebar сфокусированным на MVP: без extra settings и model controls.

Тесты:
- Component test для отправки chat message и отображения assistant reply.
- Component или integration test для применения AI-triggered board refresh.
- E2E smoke test для открытия chat, отправки message и получения response, при необходимости с mocked backend.

Критерии успеха:
- Пользователи могут общаться с AI с экрана Kanban.
- AI-triggered board updates появляются без ручного page refresh.
- Sidebar остается визуально согласованным с color scheme приложения.