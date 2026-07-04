"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { boardApi } from "@/lib/api";
import type { BoardData, Column } from "@/lib/kanban";

type KanbanBoardProps = {
  onLogout?: () => void;
};

export const KanbanBoard = ({ onLogout }: KanbanBoardProps) => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const loadBoard = useCallback(async () => {
    setError("");
    try {
      setBoard(await boardApi.getBoard());
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    }
  }, []);

  useEffect(() => {
    void loadBoard();
  }, [loadBoard]);

  const cardsById = useMemo(() => board?.cards ?? {}, [board?.cards]);

  const runBoardMutation = async (operation: () => Promise<BoardData>) => {
    setIsSaving(true);
    setError("");
    try {
      setBoard(await operation());
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!board || !over || active.id === over.id) {
      return;
    }

    const target = getMoveTarget(
      board.columns,
      active.id as string,
      over.id as string
    );
    if (!target) {
      return;
    }

    void runBoardMutation(() =>
      boardApi.moveCard(active.id as string, target.columnId, target.position)
    );
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    void runBoardMutation(() => boardApi.renameColumn(columnId, title));
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    void runBoardMutation(() => boardApi.createCard(columnId, title, details));
  };

  const handleEditCard = (cardId: string, title: string, details: string) => {
    void runBoardMutation(() => boardApi.editCard(cardId, title, details));
  };

  const handleDeleteCard = (cardId: string) => {
    void runBoardMutation(() => boardApi.deleteCard(cardId));
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  if (!board) {
    return (
      <BoardShell>
        <div className="rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
            Kanban Studio
          </p>
          <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
            Loading board
          </h1>
          {error ? (
            <div className="mt-4">
              <p role="alert" className="text-sm font-semibold text-[var(--secondary-purple)]">
                {error}
              </p>
              <button
                type="button"
                onClick={() => void loadBoard()}
                className="mt-4 rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
              >
                Retry
              </button>
            </div>
          ) : (
            <p className="mt-3 text-sm leading-6 text-[var(--gray-text)]">
              Loading your persisted board from the backend.
            </p>
          )}
        </div>
      </BoardShell>
    );
  }

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                Focus
              </p>
              <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                {isSaving
                  ? "Saving changes..."
                  : "One board. Five columns. Zero clutter."}
              </p>
              {onLogout ? (
                <button
                  type="button"
                  onClick={onLogout}
                  className="mt-4 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
                >
                  Logout
                </button>
              ) : null}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
          {error ? (
            <p role="alert" className="text-sm font-semibold text-[var(--secondary-purple)]">
              {error}
            </p>
          ) : null}
        </header>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <section className="grid gap-6 lg:grid-cols-5">
            {board.columns.map((column) => (
              <KanbanColumn
                key={column.id}
                column={column}
                cards={column.cardIds.map((cardId) => board.cards[cardId])}
                onRename={handleRenameColumn}
                onAddCard={handleAddCard}
                onEditCard={handleEditCard}
                onDeleteCard={handleDeleteCard}
              />
            ))}
          </section>
          <DragOverlay>
            {activeCard ? (
              <div className="w-[260px]">
                <KanbanCardPreview card={activeCard} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </main>
    </div>
  );
};

const BoardShell = ({ children }: { children: ReactNode }) => (
  <div className="relative overflow-hidden">
    <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
    <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col justify-center px-6 py-12">
      {children}
    </main>
  </div>
);

const getMoveTarget = (
  columns: Column[],
  activeId: string,
  overId: string
): { columnId: string; position: number } | null => {
  const targetColumn = columns.find(
    (column) => column.id === overId || column.cardIds.includes(overId)
  );
  if (!targetColumn) {
    return null;
  }

  if (targetColumn.id === overId) {
    const isSameColumn = targetColumn.cardIds.includes(activeId);
    return {
      columnId: targetColumn.id,
      position: targetColumn.cardIds.length - (isSameColumn ? 1 : 0),
    };
  }

  const withoutActive = targetColumn.cardIds.filter((cardId) => cardId !== activeId);
  const overIndex = withoutActive.indexOf(overId);

  return {
    columnId: targetColumn.id,
    position: overIndex === -1 ? withoutActive.length : overIndex,
  };
};

const getErrorMessage = (error: unknown) => {
  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong while syncing the board.";
};
