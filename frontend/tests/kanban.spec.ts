import { expect, test, type Page } from "@playwright/test";
import { initialData, type BoardData } from "../src/lib/kanban";

const cloneBoard = (): BoardData => structuredClone(initialData);

const mockBoardApi = async (page: Page, board: BoardData) => {
  await page.route("**/api/board**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();

    if (method === "GET" && path === "/api/board") {
      await route.fulfill({ json: board });
      return;
    }

    if (method === "PATCH" && path.startsWith("/api/board/columns/")) {
      const columnId = path.split("/").at(-1);
      const payload = await request.postDataJSON();
      board.columns = board.columns.map((column) =>
        column.id === columnId ? { ...column, title: payload.title } : column
      );
      await route.fulfill({ json: board });
      return;
    }

    if (method === "POST" && path === "/api/board/cards") {
      const payload = await request.postDataJSON();
      const cardId = `card-${Object.keys(board.cards).length + 1}`;
      board.cards[cardId] = {
        id: cardId,
        title: payload.title,
        details: payload.details,
      };
      board.columns = board.columns.map((column) =>
        column.id === payload.columnId
          ? { ...column, cardIds: [...column.cardIds, cardId] }
          : column
      );
      await route.fulfill({ status: 201, json: board });
      return;
    }

    if (method === "PATCH" && path.startsWith("/api/board/cards/")) {
      const cardId = path.split("/").at(-1) ?? "";
      const payload = await request.postDataJSON();
      board.cards[cardId] = { id: cardId, title: payload.title, details: payload.details };
      await route.fulfill({ json: board });
      return;
    }

    if (method === "DELETE" && path.startsWith("/api/board/cards/")) {
      const cardId = path.split("/").at(-1) ?? "";
      delete board.cards[cardId];
      board.columns = board.columns.map((column) => ({
        ...column,
        cardIds: column.cardIds.filter((id) => id !== cardId),
      }));
      await route.fulfill({ json: board });
      return;
    }

    if (method === "POST" && path.endsWith("/move")) {
      const parts = path.split("/");
      const cardId = parts.at(-2) ?? "";
      const payload = await request.postDataJSON();
      board.columns = moveCardInBoard(
        board.columns,
        cardId,
        payload.columnId,
        payload.position
      );
      await route.fulfill({ json: board });
      return;
    }

    await route.fulfill({ status: 404, json: { detail: "Not found." } });
  });
};

const signIn = async (page: Page) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
};

test("requires sign in before showing the kanban board", async ({ page }) => {
  await mockBoardApi(page, cloneBoard());
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Вход в Kanban Studio" })
  ).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(0);
});

test("rejects invalid credentials", async ({ page }) => {
  await mockBoardApi(page, cloneBoard());
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("wrong");
  await page.getByRole("button", { name: /sign in/i }).click();

  await expect(
    page.getByText("Неверное имя пользователя или пароль.")
  ).toBeVisible();
});

test("signs in and logs out", async ({ page }) => {
  await mockBoardApi(page, cloneBoard());
  await signIn(page);

  await page.getByRole("button", { name: /logout/i }).click();

  await expect(
    page.getByRole("heading", { name: "Вход в Kanban Studio" })
  ).toBeVisible();
});

test("loads the kanban board", async ({ page }) => {
  await mockBoardApi(page, cloneBoard());
  await signIn(page);

  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await mockBoardApi(page, cloneBoard());
  await signIn(page);

  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();

  await page.reload();
  await expect(page.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await mockBoardApi(page, cloneBoard());
  await signIn(page);

  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("edits a card", async ({ page }) => {
  await mockBoardApi(page, cloneBoard());
  await signIn(page);

  const card = page.getByTestId("card-card-1");
  await card.getByRole("button", { name: /edit align roadmap themes/i }).click();
  await card.getByLabel("Card title").fill("Edited in e2e");
  await card.getByLabel("Card details").fill("Persisted through mocked API.");
  await card.getByRole("button", { name: /save/i }).click();

  await expect(page.getByText("Edited in e2e")).toBeVisible();
});

const moveCardInBoard = (
  columns: BoardData["columns"],
  cardId: string,
  columnId: string,
  position: number
) => {
  const nextColumns = columns.map((column) => ({
    ...column,
    cardIds: column.cardIds.filter((id) => id !== cardId),
  }));
  return nextColumns.map((column) => {
    if (column.id !== columnId) {
      return column;
    }

    const cardIds = [...column.cardIds];
    cardIds.splice(position, 0, cardId);
    return { ...column, cardIds };
  });
};
