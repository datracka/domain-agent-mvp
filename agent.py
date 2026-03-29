"""
PerformMax AI Agent

Implements the agentic loop using the Anthropic Claude API with tool use.

Flow per user message:
  1. Append the user message to the session history.
  2. Call Claude (streaming) with the full history + tool schemas.
  3. Stream text tokens back to the caller as SSE events.
  4. If Claude requests tool calls, execute them and feed results back — repeat.
  5. When stop_reason == "end_turn", yield a "done" SSE event and exit the loop.
"""

import json
import anthropic
from tools import TOOLS, execute_tool

# ─────────────────────────────────────────────
# Anthropic async client (reads ANTHROPIC_API_KEY from environment)
# ─────────────────────────────────────────────
client = anthropic.AsyncAnthropic()

# ─────────────────────────────────────────────
# Domain system prompt
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are PerformMax AI, an expert performance marketing assistant embedded in the PerformMax platform.
Your job is to help marketing professionals maximise ROI, optimise ad spend, and grow their business.

## Your expertise
- Search advertising (Google Ads, Microsoft Ads)
- Social media advertising (Meta, TikTok, LinkedIn, X)
- Display & programmatic campaigns
- Email marketing automation
- Video advertising (YouTube, Meta Reels, TikTok)
- Attribution modelling, A/B testing, conversion rate optimisation
- Budget allocation and bid strategy

## Platform capabilities
You have access to three tools that connect to real PerformMax backend services:

1. **register_or_login_user** — Create or authenticate a user account.
2. **process_payment** — Handle subscription purchases (Starter / Professional / Enterprise).
3. **get_marketing_recommendations** — Call our RAG service to retrieve personalised, data-driven
   recommendations based on campaign type, budget, and goals.

## Behaviour guidelines
- Call tools proactively when they would help the user — don't ask for permission each time.
- Before processing a payment always confirm the user is authenticated (has a user_id).
- When giving recommendations, gather campaign type, budget, and goals first if not provided.
- After every tool call, interpret the result in plain language — don't just dump raw JSON at the user.
- Be concise, actionable, and professional.
"""

# ─────────────────────────────────────────────
# In-memory session store  (replace with Redis / DB for production)
# ─────────────────────────────────────────────
sessions: dict[str, list[dict]] = {}


# ─────────────────────────────────────────────
# SSE helper
# ─────────────────────────────────────────────
def _sse(payload: dict) -> str:
    """Format a dict as a Server-Sent Event string."""
    return f"data: {json.dumps(payload)}\n\n"


# ─────────────────────────────────────────────
# Main agent coroutine
# ─────────────────────────────────────────────
async def chat_stream(session_id: str, user_message: str):
    """
    Async generator that runs the agentic loop and yields SSE strings.

    SSE event types emitted:
      {"type": "text",        "content": "<token>"}     — streamed text from Claude
      {"type": "tool_call",   "tool": "<name>", "input": {...}}  — about to call a tool
      {"type": "tool_result", "tool": "<name>", "result": {...}} — tool returned
      {"type": "error",       "message": "<msg>"}       — unrecoverable error
      {"type": "done"}                                   — conversation turn complete
    """
    # Initialise or restore session history
    if session_id not in sessions:
        sessions[session_id] = []

    messages = sessions[session_id]
    messages.append({"role": "user", "content": user_message})

    # ── Agentic loop ──────────────────────────────────────────────────────────
    try:
        while True:
            # Stream Claude's response
            async with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
                # Adaptive thinking lets Claude decide when extra reasoning helps.
                # We skip it for chat turns to keep latency low, but you could
                # enable it with: thinking={"type": "adaptive"}
            ) as stream:

                async for event in stream:
                    # Stream text tokens to the client in real-time
                    if (
                        event.type == "content_block_delta"
                        and event.delta.type == "text_delta"
                    ):
                        yield _sse({"type": "text", "content": event.delta.text})

                # Collect the full response once streaming is done
                response = await stream.get_final_message()

            # Append assistant turn to history
            messages.append({"role": "assistant", "content": response.content})

            # ── Done? ─────────────────────────────────────────────────────────
            if response.stop_reason == "end_turn":
                break

            # ── Tool use? ─────────────────────────────────────────────────────
            if response.stop_reason == "tool_use":
                tool_results = []

                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    # Notify the client that we are about to call a tool
                    yield _sse({
                        "type": "tool_call",
                        "tool": block.name,
                        "input": block.input,
                    })

                    # Execute the (fake) tool
                    raw_result = execute_tool(block.name, block.input)
                    parsed_result = json.loads(raw_result)

                    # Notify the client of the tool result
                    yield _sse({
                        "type": "tool_result",
                        "tool": block.name,
                        "result": parsed_result,
                    })

                    # Package for the next Claude turn
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": raw_result,
                    })

                # Feed tool results back as a user message and loop again
                messages.append({"role": "user", "content": tool_results})

            else:
                # Unexpected stop reason — exit gracefully
                break

    except anthropic.APIError as exc:
        yield _sse({"type": "error", "message": str(exc)})

    finally:
        # Persist updated history
        sessions[session_id] = messages
        yield _sse({"type": "done"})
