from __future__ import annotations

"""
Simple test client that exercises the agent API.

Run the server first:
  uvicorn main:app --reload

Then run this script:
  python test_client.py
"""

import json
import sys
import httpx

BASE_URL = "http://localhost:8000"


def chat(message: str, session_id: str | None = None) -> str:
    """
    Send a message and print the SSE stream as it arrives.
    Returns the session_id for follow-up messages.
    """
    print(f"\n{'─' * 60}")
    print(f"YOU: {message}")
    print(f"{'─' * 60}")
    print("AGENT: ", end="", flush=True)

    returned_session_id = session_id
    full_text = []

    with httpx.Client(timeout=120) as client:
        with client.stream(
            "POST",
            f"{BASE_URL}/chat",
            json={"message": message, "session_id": session_id},
        ) as response:
            response.raise_for_status()
            returned_session_id = response.headers.get("x-session-id", session_id)

            for line in response.iter_lines():
                if not line.startswith("data: "):
                    continue
                payload = json.loads(line[6:])

                t = payload["type"]
                if t == "text":
                    print(payload["content"], end="", flush=True)
                    full_text.append(payload["content"])

                elif t == "tool_call":
                    print(
                        f"\n\n  ⚙  Tool call → {payload['tool']}"
                        f"\n     Input: {json.dumps(payload['input'], indent=6)}\n",
                        flush=True,
                    )

                elif t == "tool_result":
                    print(
                        f"\n  ✓  Tool result ← {payload['tool']}"
                        f"\n     Result: {json.dumps(payload['result'], indent=6)}\n",
                        flush=True,
                    )

                elif t == "error":
                    print(f"\n  ✗  Error: {payload['message']}", flush=True)

                elif t == "done":
                    print()  # newline after streaming

    return returned_session_id


def main():
    print("PerformMax AI — test client")
    print("=" * 60)

    # ── Turn 1: general greeting / capability question ─────────────────
    sid = chat("Hi! What can you help me with?")

    # ── Turn 2: ask for recommendations (triggers tool call) ───────────
    sid = chat(
        "I'm running a social media campaign on Meta with a $5,000/month budget. "
        "My main goals are to increase conversions and improve ROAS. "
        "My user ID is usr_demo123. Can you get me some recommendations?",
        session_id=sid,
    )

    # ── Turn 3: ask about pricing / registration ────────────────────────
    sid = chat(
        "That's helpful! I'd like to sign up for the Professional plan. "
        "My email is alice@example.com and my password is SecurePass42.",
        session_id=sid,
    )

    # ── Turn 4: subscribe after registration ───────────────────────────
    sid = chat(
        "Great, I'm registered. Now please subscribe me to the Professional plan "
        "with monthly billing using my credit card.",
        session_id=sid,
    )

    print("\n" + "=" * 60)
    print(f"Final session ID: {sid}")


if __name__ == "__main__":
    main()
