"""
PerformMax AI — FastAPI entry point

Endpoints:
  GET  /               health check
  POST /chat           send a message, receive SSE stream
  GET  /sessions       list active session IDs
  DELETE /sessions/{id} clear a session's history
"""

import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()  # loads ANTHROPIC_API_KEY from .env if present

from agent import chat_stream, sessions  # noqa: E402 (import after env load)


# ─────────────────────────────────────────────
# App
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("PerformMax AI agent started.")
    yield
    print("Shutting down.")


app = FastAPI(
    title="PerformMax AI Agent",
    description=(
        "A performance-marketing domain agent powered by Claude Opus 4.6. "
        "Supports user auth, payments, and RAG-based campaign recommendations."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Session-ID"],
)


# ─────────────────────────────────────────────
# Request / response schemas
# ─────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  # omit to start a new session


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.get("/")
async def health():
    return {
        "status": "ok",
        "agent": "PerformMax AI",
        "model": "claude-opus-4-6",
        "active_sessions": len(sessions),
    }


@app.post(
    "/chat",
    summary="Send a message to the agent",
    description=(
        "Returns a Server-Sent Events stream. Each event is a JSON object with a `type` field:\n\n"
        "- `text` — streamed text token from Claude (`content` field)\n"
        "- `tool_call` — the agent is invoking a tool (`tool`, `input` fields)\n"
        "- `tool_result` — the tool returned (`tool`, `result` fields)\n"
        "- `error` — something went wrong (`message` field)\n"
        "- `done` — the turn is complete\n\n"
        "The response header `X-Session-ID` contains the session ID to use in follow-up requests."
    ),
)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())

    return StreamingResponse(
        chat_stream(session_id, request.message),
        media_type="text/event-stream",
        headers={
            "X-Session-ID": session_id,
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/sessions", summary="List active session IDs")
async def list_sessions():
    return {
        "sessions": [
            {"id": sid, "turns": len(msgs) // 2}
            for sid, msgs in sessions.items()
        ]
    }


@app.delete("/sessions/{session_id}", summary="Clear a session's history")
async def clear_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    del sessions[session_id]
    return {"cleared": True, "session_id": session_id}
