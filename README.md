# PerformMax AI Agent

A teaching demo of a domain-specific AI agent built with **FastAPI** and **Claude Opus 4.6**. It shows how to structure an agentic loop with tool use, SSE streaming, and multi-turn session management.

> **Note:** All backend services (auth, payments, RAG) are stubs returning realistic fake data. This project is for learning agent architecture — not production use.

## Architecture

```
Client (HTTP/SSE)
      │
      ▼
main.py  ── FastAPI app (routing, CORS, SSE response)
      │
      ▼
agent.py ── Agentic loop (stream Claude → detect tool_use → execute → repeat)
      │
      ▼
tools.py ── Tool schemas (sent to Claude) + fake implementations
```

**Agentic loop flow:**
1. Append user message to session history
2. Stream Claude's response, forwarding text tokens as SSE events
3. If `stop_reason == "tool_use"`, execute the tool(s) and feed results back
4. Repeat until `stop_reason == "end_turn"`

## Tools

| Tool | Description |
|------|-------------|
| `register_or_login_user` | Fake auth — register or log in a user |
| `process_payment` | Fake payment — Starter $49 / Professional $149 / Enterprise $499/mo |
| `get_marketing_recommendations` | Fake RAG — returns campaign-specific benchmarks and quick wins |

## SSE Event Types

The `/chat` endpoint streams newline-delimited JSON events:

| Type | Fields | Description |
|------|--------|-------------|
| `text` | `content` | Streamed text token from Claude |
| `tool_call` | `tool`, `input` | Agent is invoking a tool |
| `tool_result` | `tool`, `result` | Tool returned a result |
| `error` | `message` | Unrecoverable error |
| `done` | — | Turn complete |

## Setup

**Requirements:** Python 3.11+

```bash
# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=your-api-key-here
```

## Running

```bash
# Start the server
uvicorn main:app --reload

# In a separate terminal, run the multi-turn demo
python test_client.py
```

The server starts at `http://localhost:8000`. Interactive API docs are at `http://localhost:8000/docs`.

## API Reference

### `GET /`
Health check. Returns agent status and active session count.

### `POST /chat`
Send a message; receive an SSE stream.

**Request body:**
```json
{
  "message": "I need help with my ad campaign",
  "session_id": "optional-existing-session-id"
}
```

**Response headers:** `X-Session-ID` — use this in follow-up requests to continue the conversation.

### `GET /sessions`
List all active session IDs and their turn counts.

### `DELETE /sessions/{session_id}`
Clear a session's message history.

## Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app — routes, middleware, request/response schemas |
| `agent.py` | Agentic loop and SSE formatting |
| `tools.py` | Tool JSON schemas + fake service implementations |
| `test_client.py` | httpx-based test client demonstrating a 4-turn conversation |
| `.env.example` | Environment variable template |
| `requirements.txt` | Python dependencies |

## Key Concepts Demonstrated

- **Tool use with the Anthropic SDK** — defining schemas and dispatching calls
- **Streaming with `client.messages.stream()`** — forwarding tokens in real time
- **Agentic loop** — how to handle multi-step tool chains before a final answer
- **SSE from FastAPI** — `StreamingResponse` with `text/event-stream`
- **Session management** — in-memory history (swap for Redis/DB in production)
