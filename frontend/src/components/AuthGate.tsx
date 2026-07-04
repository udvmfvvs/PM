"use client";

import { useState, useSyncExternalStore, type FormEvent } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";

const SESSION_KEY = "pm:mvp-session";
const AUTH_CHANGED_EVENT = "pm:auth-changed";
const VALID_USERNAME = "user";
const VALID_PASSWORD = "password";

type LoginState = {
  username: string;
  password: string;
};

const initialLoginState: LoginState = { username: "", password: "" };

export const AuthGate = () => {
  const isSignedIn = useSyncExternalStore(
    subscribeToAuthChanges,
    getAuthSnapshot,
    () => false
  );
  const [loginState, setLoginState] = useState(initialLoginState);
  const [error, setError] = useState("");

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (
      loginState.username === VALID_USERNAME &&
      loginState.password === VALID_PASSWORD
    ) {
      window.localStorage.setItem(SESSION_KEY, "signed-in");
      window.dispatchEvent(new Event(AUTH_CHANGED_EVENT));
      setLoginState(initialLoginState);
      setError("");
      return;
    }

    setError("Неверное имя пользователя или пароль.");
  };

  const handleLogout = () => {
    window.localStorage.removeItem(SESSION_KEY);
    window.dispatchEvent(new Event(AUTH_CHANGED_EVENT));
  };

  if (isSignedIn) {
    return <KanbanBoard onLogout={handleLogout} />;
  }

  return (
    <main className="relative mx-auto flex min-h-screen max-w-[720px] items-center px-6 py-12">
      <div className="pointer-events-none absolute left-0 top-0 h-[360px] w-[360px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <section className="relative w-full rounded-[32px] border border-[var(--stroke)] bg-white/85 p-8 shadow-[var(--shadow)] backdrop-blur">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
          Project Management MVP
        </p>
        <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
          Вход в Kanban Studio
        </h1>
        <p className="mt-3 text-sm leading-6 text-[var(--gray-text)]">
          Войдите с dummy credentials, чтобы открыть локальную Kanban board.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <div>
            <label
              htmlFor="username"
              className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
            >
              Username
            </label>
            <input
              id="username"
              value={loginState.username}
              onChange={(event) =>
                setLoginState((prev) => ({
                  ...prev,
                  username: event.target.value,
                }))
              }
              className="mt-2 w-full rounded-2xl border border-[var(--stroke)] bg-white px-4 py-3 text-sm font-medium text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
              autoComplete="username"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={loginState.password}
              onChange={(event) =>
                setLoginState((prev) => ({
                  ...prev,
                  password: event.target.value,
                }))
              }
              className="mt-2 w-full rounded-2xl border border-[var(--stroke)] bg-white px-4 py-3 text-sm font-medium text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
              autoComplete="current-password"
            />
          </div>

          {error ? (
            <p role="alert" className="text-sm font-semibold text-[var(--secondary-purple)]">
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            className="w-full rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-sm font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
          >
            Sign in
          </button>
        </form>
      </section>
    </main>
  );
};

const getAuthSnapshot = () => {
  if (typeof window === "undefined") {
    return false;
  }

  return window.localStorage.getItem(SESSION_KEY) === "signed-in";
};

const subscribeToAuthChanges = (onStoreChange: () => void) => {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener(AUTH_CHANGED_EVENT, onStoreChange);

  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener(AUTH_CHANGED_EVENT, onStoreChange);
  };
};
