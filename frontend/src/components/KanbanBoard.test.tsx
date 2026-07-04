import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, vi } from "vitest";
import { KanbanBoard } from "@/components/KanbanBoard";
import { boardApi } from "@/lib/api";
import { initialData, type BoardData } from "@/lib/kanban";

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

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];
const cloneBoard = (board: BoardData = initialData): BoardData =>
  structuredClone(board);

describe("KanbanBoard", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mockedBoardApi.getBoard.mockResolvedValue(cloneBoard());
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
});
