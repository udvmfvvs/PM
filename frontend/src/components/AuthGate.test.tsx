import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, vi } from "vitest";
import { AuthGate } from "@/components/AuthGate";
import { boardApi } from "@/lib/api";
import { initialData } from "@/lib/kanban";

vi.mock("@/lib/api", () => ({
  boardApi: {
    getBoard: vi.fn(),
    renameColumn: vi.fn(),
    createCard: vi.fn(),
    editCard: vi.fn(),
    deleteCard: vi.fn(),
    moveCard: vi.fn(),
  },
}));

const mockedBoardApi = vi.mocked(boardApi);

describe("AuthGate", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    window.localStorage.clear();
    mockedBoardApi.getBoard.mockResolvedValue(structuredClone(initialData));
  });

  it("shows an error for invalid credentials", async () => {
    render(<AuthGate />);
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("Username"), "wrong");
    await user.type(screen.getByLabelText("Password"), "password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Неверное имя пользователя или пароль."
    );
    expect(
      screen.queryByRole("heading", { name: "Kanban Studio" })
    ).not.toBeInTheDocument();
  });

  it("shows the board after valid credentials and logs out", async () => {
    render(<AuthGate />);
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("Username"), "user");
    await user.type(screen.getByLabelText("Password"), "password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(
      await screen.findByRole("heading", { name: "Kanban Studio" })
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /logout/i }));

    expect(
      screen.getByRole("heading", { name: "Вход в Kanban Studio" })
    ).toBeInTheDocument();
  });
});
