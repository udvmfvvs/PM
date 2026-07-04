import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


def create_app(static_dir: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="Project Management MVP")

    @app.get("/api/health")
    def read_health() -> dict[str, str]:
        return {"status": "ok"}

    static_path = _resolve_static_dir(static_dir)
    if (static_path / "index.html").exists():
        app.mount("/", StaticFiles(directory=static_path, html=True), name="frontend")
        return app

    @app.get("/", response_class=HTMLResponse)
    def read_root() -> str:
        return """
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>Project Management MVP</title>
          </head>
          <body>
            <main>
              <h1>Project Management MVP</h1>
              <p>Hello from the FastAPI backend.</p>
            </main>
          </body>
        </html>
        """

    return app


def _resolve_static_dir(static_dir: str | Path | None) -> Path:
    if static_dir is not None:
        return Path(static_dir)

    configured_dir = os.getenv("FRONTEND_STATIC_DIR")
    if configured_dir:
        return Path(configured_dir)

    return Path(__file__).resolve().parent.parent / "static"


app = create_app()
