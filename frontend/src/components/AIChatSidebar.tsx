"use client";

import { useState, type FormEvent } from "react";
import { aiApi, type AIChatMessage } from "@/lib/api";
import type { BoardData } from "@/lib/kanban";

type AIChatSidebarProps = {
  onBoardUpdate: (board: BoardData) => void;
};

export const AIChatSidebar = ({ onBoardUpdate }: AIChatSidebarProps) => {
  const [messages, setMessages] = useState<AIChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const [isSending, setIsSending] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const userMessage = draft.trim();
    if (!userMessage || isSending) {
      return;
    }

    const history = messages;
    setMessages([...history, { role: "user", content: userMessage }]);
    setDraft("");
    setError("");
    setIsSending(true);

    try {
      const response = await aiApi.chat(userMessage, history);
      setMessages([
        ...history,
        { role: "user", content: userMessage },
        { role: "assistant", content: response.message },
      ]);
      if (response.board) {
        onBoardUpdate(response.board);
      }
    } catch (caughtError) {
      setMessages(history);
      setDraft(userMessage);
      setError(getErrorMessage(caughtError));
    } finally {
      setIsSending(false);
    }
  };

  return (
    <aside className="flex min-h-[520px] flex-col rounded-[32px] border border-[var(--stroke)] bg-white/85 p-5 shadow-[var(--shadow)] backdrop-blur">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
          AI Assistant
        </p>
        <h2 className="mt-2 font-display text-2xl font-semibold text-[var(--navy-dark)]">
          Board helper
        </h2>
        <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
          Ask for card edits, moves, or a quick planning note.
        </p>
      </div>

      <div
        aria-live="polite"
        className="mt-5 flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto rounded-3xl bg-[var(--surface)] p-4"
      >
        {messages.length ? (
          messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={
                message.role === "user"
                  ? "self-end rounded-3xl bg-[var(--primary-blue)] px-4 py-3 text-sm leading-6 text-white"
                  : "self-start rounded-3xl border border-[var(--stroke)] bg-white px-4 py-3 text-sm leading-6 text-[var(--navy-dark)]"
              }
            >
              {message.content}
            </div>
          ))
        ) : (
          <p className="rounded-3xl border border-dashed border-[var(--stroke)] bg-white px-4 py-3 text-sm leading-6 text-[var(--gray-text)]">
            Try: “Create a card for release notes in Backlog.”
          </p>
        )}
      </div>

      {error ? (
        <p role="alert" className="mt-4 text-sm font-semibold text-[var(--secondary-purple)]">
          {error}
        </p>
      ) : null}

      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <label
          htmlFor="ai-message"
          className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]"
        >
          Message AI
        </label>
        <textarea
          id="ai-message"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          rows={4}
          placeholder="Ask AI to update the board..."
          className="w-full resize-none rounded-3xl border border-[var(--stroke)] bg-white px-4 py-3 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
        />
        <button
          type="submit"
          disabled={isSending || !draft.trim()}
          className="w-full rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-sm font-semibold uppercase tracking-wide text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSending ? "Sending..." : "Send message"}
        </button>
      </form>
    </aside>
  );
};

const getErrorMessage = (error: unknown) => {
  if (error instanceof Error) {
    return error.message;
  }

  return "AI request failed.";
};
