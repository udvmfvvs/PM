import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthGate } from "@/components/AuthGate";

describe("AuthGate", () => {
  beforeEach(() => {
    window.localStorage.clear();
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
      screen.getByRole("heading", { name: "Kanban Studio" })
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /logout/i }));

    expect(
      screen.getByRole("heading", { name: "Вход в Kanban Studio" })
    ).toBeInTheDocument();
  });
});
