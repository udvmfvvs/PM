# Дизайн базы данных

## Цель

Для MVP база данных хранит один Kanban board для signed-in user `user`. При этом schema должна оставлять простой путь к нескольким пользователям и нескольким boards в будущем.

Backend использует SQLite. Если database file отсутствует, backend создает его автоматически и seed-ит default board для MVP user.

## JSON-формат board

Этот JSON-формат используется API, frontend и AI. Порядок columns задается порядком элементов в `columns`. Порядок cards внутри column задается массивом `cardIds`.

```json
{
  "id": "board-default",
  "userId": "user",
  "columns": [
    {
      "id": "col-backlog",
      "title": "Backlog",
      "cardIds": ["card-1", "card-2"]
    }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Align roadmap themes",
      "details": "Draft quarterly themes with impact statements and metrics."
    },
    "card-2": {
      "id": "card-2",
      "title": "Gather customer signals",
      "details": "Review support tags, sales notes, and churn feedback."
    }
  }
}
```

## SQLite schema

Для MVP используем нормализованную schema. Это проще проверять и обновлять, чем хранить весь board одним JSON blob.

### `users`

Хранит пользователей. В MVP создается только пользователь `user`.

```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### `boards`

Хранит boards. В MVP у пользователя один board, что фиксируется `UNIQUE (user_id)`.

```sql
CREATE TABLE boards (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  title TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE (user_id)
);
```

### `columns`

Хранит fixed columns board. Columns можно переименовывать, но для MVP не нужно создавать или удалять columns. Порядок columns хранится в `position`.

```sql
CREATE TABLE columns (
  id TEXT PRIMARY KEY,
  board_id TEXT NOT NULL,
  title TEXT NOT NULL,
  position INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
  UNIQUE (board_id, position)
);
```

### `cards`

Хранит cards. Принадлежность card к column и порядок внутри column хранятся в `column_id` и `position`.

```sql
CREATE TABLE cards (
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
```

## Initial data

Если database file отсутствует или в нем нет пользователя `user`, backend создает:

- `users` row:
  - `id`: `user`
  - `username`: `user`
- один board:
  - `id`: `board-default`
  - `user_id`: `user`
  - `title`: `Project Board`
- пять fixed columns:
  - `col-backlog`
  - `col-discovery`
  - `col-progress`
  - `col-review`
  - `col-done`
- initial cards, соответствующие текущему frontend `initialData`.

Seed должен быть idempotent: повторный startup не должен дублировать users, boards, columns или cards.

## Read behavior

`GET` board endpoint читает строки из `boards`, `columns` и `cards`, затем собирает JSON:

- `columns` сортируются по `columns.position`;
- `cards` группируются по `column_id` и сортируются по `cards.position`;
- каждый `column.cardIds` строится из отсортированных cards этой column;
- `cards` возвращается как object, где key равен `card.id`.

## Update behavior

Обновления должны проходить через backend API, а не прямую замену database file.

### Rename column

- Проверить, что `column_id` принадлежит board текущего user.
- Обновить `columns.title`.
- Обновить `columns.updated_at` и `boards.updated_at`.

### Create card

- Проверить, что target column принадлежит board текущего user.
- Создать card с новым `id`.
- Поставить `position` в конец target column.
- Обновить `boards.updated_at`.

### Edit card

- Проверить, что card принадлежит board текущего user.
- Обновить `title` и `details`.
- Обновить `cards.updated_at` и `boards.updated_at`.

### Delete card

- Проверить, что card принадлежит board текущего user.
- Удалить card.
- Перенумеровать `position` оставшихся cards в column без gaps.
- Обновить `boards.updated_at`.

### Move card

- Проверить, что card, source column и target column принадлежат board текущего user.
- В transaction:
  - удалить card из старой позиции;
  - вставить card в target column на новую позицию;
  - перенумеровать `position` в затронутых columns без gaps;
  - обновить `cards.column_id`, `cards.position`, `cards.updated_at` и `boards.updated_at`.

## Constraints

- `users.username` уникален.
- Для MVP `boards.user_id` уникален, чтобы у user был один board.
- `columns.position` уникален внутри board.
- `cards.position` уникален внутри column.
- `title` для columns и cards не должен быть пустым после trim.
- `details` может быть пустой строкой.
- Backend должен включить SQLite foreign keys через `PRAGMA foreign_keys = ON`.

## AI compatibility

AI получает и возвращает тот же board JSON, что использует frontend. Любые AI-generated updates должны применяться через backend update rules, а не напрямую записывать произвольный JSON в database.

Это сохраняет invariants:

- card не может ссылаться на несуществующую column;
- `cardIds` всегда соответствуют real cards;
- ordering хранится в одном месте, через `position`;
- persisted board нельзя повредить malformed AI response.
