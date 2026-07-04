# MVP веб-приложения для управления проектами

## Бизнес-требования

Этот проект создает Project Management App. Ключевые возможности:
- Пользователь может войти в систему.
- После входа пользователь видит Kanban board, представляющий его проект.
- Kanban board имеет фиксированные columns, которые можно переименовывать.
- Cards на Kanban board можно перемещать drag and drop и редактировать.
- В sidebar есть AI chat; AI может создавать, редактировать или перемещать одну или несколько cards.

## Ограничения

Для MVP будет только вход пользователя с hardcoded credentials `user` и `password`, но database должна поддерживать нескольких пользователей в будущем.

Для MVP у каждого signed-in user будет только один Kanban board.

Для MVP приложение будет запускаться локально в docker container.

## Технические решения

- NextJS frontend.
- Python FastAPI backend, включая отдачу статического NextJS site на `/`.
- Все упаковано в Docker container.
- Использовать `uv` как package manager для Python в Docker container.
- Использовать OpenRouter для AI calls. `OPENROUTER_API_KEY` находится в `.env` в корне проекта.
- Использовать `openai/gpt-oss-120b` как модель.
- Использовать локальную SQLite database, создавая новую database, если она не существует.
- Скрипты Start и Stop server для Mac, PC и Linux находятся в `scripts/`.

## Начальная точка

Рабочий MVP frontend уже создан и находится в `frontend`. Он еще не адаптирован под Docker setup. Сейчас это чистый frontend-only demo.

## Цветовая схема

- Accent Yellow: `#ecad0a` - accent lines, highlights.
- Blue Primary: `#209dd7` - links, key sections.
- Purple Secondary: `#753991` - submit buttons, important actions.
- Dark Navy: `#032147` - main headings.
- Gray Text: `#888888` - supporting text, labels.

## Стандарты кодирования

1. Использовать актуальные версии libraries и idiomatic approaches на сегодняшний день.
2. Делать просто: NEVER over-engineer, ALWAYS simplify, NO unnecessary defensive programming. Никаких extra features, фокус на простоте.
3. Быть кратким. Держать README минимальным. IMPORTANT: никаких emojis никогда.
4. При возникновении проблем всегда сначала определить root cause перед исправлением. Не угадывать. Доказать фактами, затем исправить root cause.

## Рабочая документация

Все документы для планирования и выполнения проекта должны находиться в директории `docs/`.
Перед продолжением необходимо изучить документ `docs/PLAN.md`.