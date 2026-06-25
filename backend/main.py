"""FastAPI-App: stellt die Weboberfläche bereit und nimmt Chat-Anfragen entgegen."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import get_settings
from .home_assistant import get_home_assistant
from .jarvis import get_jarvis

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="Jarvis", description="Assistent im Stil von Iron Mans J.A.R.V.I.S.")

# Sehr einfacher In-Memory-Speicher der Gesprächsverläufe je Session.
# Für den Einzelnutzer-Heimbetrieb ausreichend; bei Neustart wird er geleert.
_sessions: dict[str, list[dict]] = {}
MAX_HISTORY = 40  # letzte N Nachrichten je Session behalten


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@app.get("/api/health")
async def health() -> dict:
    settings = get_settings()
    return {
        "status": "online",
        "claude_ready": settings.claude_ready,
        "model": settings.jarvis_model,
        "home_assistant_configured": settings.home_assistant_ready,
    }


@app.get("/api/home-assistant/status")
async def ha_status() -> dict:
    ha = get_home_assistant()
    if not ha.enabled:
        return {"configured": False, "connected": False}
    connected = await ha.ping()
    return {"configured": True, "connected": connected}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    session_id = req.session_id or uuid.uuid4().hex
    history = _sessions.setdefault(session_id, [])

    history.append({"role": "user", "content": req.message})

    jarvis = get_jarvis()
    reply = await jarvis.respond(history)

    history.append({"role": "assistant", "content": reply})

    # Verlauf begrenzen, damit er nicht unbegrenzt wächst.
    if len(history) > MAX_HISTORY:
        del history[:-MAX_HISTORY]

    return ChatResponse(reply=reply, session_id=session_id)


@app.post("/api/reset")
async def reset(req: ChatRequest) -> JSONResponse:
    if req.session_id and req.session_id in _sessions:
        _sessions[req.session_id].clear()
    return JSONResponse({"ok": True})


# ── Statische Weboberfläche ──────────────────────────────────────────
@app.get("/")
async def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")


def main() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
