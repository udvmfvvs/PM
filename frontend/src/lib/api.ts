import type { BoardData } from "@/lib/kanban";

type RequestOptions = {
  method?: string;
  body?: unknown;
};

const requestBoard = async (
  path: string,
  options: RequestOptions = {}
): Promise<BoardData> => {
  const response = await fetch(path, {
    method: options.method ?? "GET",
    headers: options.body ? { "Content-Type": "application/json" } : undefined,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new Error(message);
  }

  return response.json();
};

const readErrorMessage = async (response: Response) => {
  try {
    const payload = await response.json();
    return payload.detail || "Board request failed.";
  } catch {
    return "Board request failed.";
  }
};

export const boardApi = {
  getBoard: () => requestBoard("/api/board"),
  renameColumn: (columnId: string, title: string) =>
    requestBoard(`/api/board/columns/${columnId}`, {
      method: "PATCH",
      body: { title },
    }),
  createCard: (columnId: string, title: string, details: string) =>
    requestBoard("/api/board/cards", {
      method: "POST",
      body: { columnId, title, details },
    }),
  editCard: (cardId: string, title: string, details: string) =>
    requestBoard(`/api/board/cards/${cardId}`, {
      method: "PATCH",
      body: { title, details },
    }),
  deleteCard: (cardId: string) =>
    requestBoard(`/api/board/cards/${cardId}`, { method: "DELETE" }),
  moveCard: (cardId: string, columnId: string, position: number) =>
    requestBoard(`/api/board/cards/${cardId}/move`, {
      method: "POST",
      body: { columnId, position },
    }),
};
