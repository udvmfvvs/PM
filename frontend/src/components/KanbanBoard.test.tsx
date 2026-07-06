import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, vi } from "vitest";
import { KanbanBoard } from "@/components/KanbanBoard";
import { aiApi, boardApi } from "@/lib/api";
import { initialData, type BoardData } from "@/lib/kanban";

vi.mock("@/lib/api", () => ({
  aiApi: {
    chat: vi.fn(),
  },
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
const mockedAIApi = vi.mocked(aiApi);

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];
const cloneBoard = (board: BoardData = initialData): BoardData =>
  structuredClone(board);

describe("KanbanBoard", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mockedBoardApi.getBoard.mockResolvedValue(cloneBoard());
    mockedAIApi.chat.mockResolvedValue({
      message: "No board changes needed.",
      board: null,
    });
  });

  it("renders API-loaded board data", async () => {
    render(<KanbanBoard />);

    expect(await screen.findByText("Backlog")).toBeInTheDocument();
    expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    expect(mockedBoardApi.getBoard).toHaveBeenCalledOnce();
  });

  it("renames a column", async () => {
    const renamedBoard = cloneBoard();
    renamedBoard.columns[0].title = "New Name";
    mockedBoardApi.renameColumn.mockResolvedValue(renamedBoard);

    render(<KanbanBoard />);
    const column = await screen.findByTestId("column-col-backlog");
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    await userEvent.tab();

    await waitFor(() =>
      expect(mockedBoardApi.renameColumn).toHaveBeenCalledWith(
        "col-backlog",
        "New Name"
      )
    );
    expect(await screen.findByDisplayValue("New Name")).toBeInTheDocument();
  });

  it("adds and removes a card", async () => {
    const boardWithNewCard = cloneBoard();
    boardWithNewCard.cards["card-new"] = {
      id: "card-new",
      title: "New card",
      details: "Notes",
    };
    boardWithNewCard.columns[0].cardIds.push("card-new");
    mockedBoardApi.createCard.mockResolvedValue(boardWithNewCard);
    const boardAfterDelete = cloneBoard();
    mockedBoardApi.deleteCard.mockResolvedValue(boardAfterDelete);

    render(<KanbanBoard />);
    await screen.findByText("Backlog");
    const column = getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(within(column).getByText("New card")).toBeInTheDocument();
    expect(mockedBoardApi.createCard).toHaveBeenCalledWith(
      "col-backlog",
      "New card",
      "Notes"
    );

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
    expect(mockedBoardApi.deleteCard).toHaveBeenCalledWith("card-new");
  });

  it("edits a card", async () => {
    const editedBoard = cloneBoard();
    editedBoard.cards["card-1"] = {
      id: "card-1",
      title: "Edited card",
      details: "Edited details",
    };
    mockedBoardApi.editCard.mockResolvedValue(editedBoard);

    render(<KanbanBoard />);
    const card = await screen.findByTestId("card-card-1");

    await userEvent.click(
      within(card).getByRole("button", { name: /edit align roadmap themes/i })
    );
    await userEvent.clear(within(card).getByLabelText("Card title"));
    await userEvent.type(within(card).getByLabelText("Card title"), "Edited card");
    await userEvent.clear(within(card).getByLabelText("Card details"));
    await userEvent.type(within(card).getByLabelText("Card details"), "Edited details");
    await userEvent.click(within(card).getByRole("button", { name: /save/i }));

    expect(mockedBoardApi.editCard).toHaveBeenCalledWith(
      "card-1",
      "Edited card",
      "Edited details"
    );
    expect(screen.getByText("Edited card")).toBeInTheDocument();
  });

  it("sends a chat message and displays the assistant reply", async () => {
    mockedAIApi.chat.mockResolvedValue({
      message: "I can help with that.",
      board: null,
    });

    render(<KanbanBoard />);
    await screen.findByText("Backlog");
    await userEvent.type(
      screen.getByLabelText("Message AI"),
      "What should I work on next?"
    );
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));

    await waitFor(() =>
      expect(mockedAIApi.chat).toHaveBeenCalledWith(
        "What should I work on next?",
        []
      )
    );
    expect(await screen.findByText("I can help with that.")).toBeInTheDocument();
  });

  it("applies an AI-updated board without a reload", async () => {
    const updatedBoard = cloneBoard();
    updatedBoard.cards["card-ai"] = {
      id: "card-ai",
      title: "AI-created card",
      details: "Added through chat.",
    };
    updatedBoard.columns[0].cardIds.push("card-ai");
    mockedAIApi.chat.mockResolvedValue({
      message: "Added a card.",
      board: updatedBoard,
    });

    render(<KanbanBoard />);
    await screen.findByText("Backlog");
    await userEvent.type(screen.getByLabelText("Message AI"), "Add a card");
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));

    expect(await screen.findByText("AI-created card")).toBeInTheDocument();
    expect(mockedBoardApi.getBoard).toHaveBeenCalledOnce();
  });
});
