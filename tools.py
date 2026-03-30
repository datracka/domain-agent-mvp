from __future__ import annotations

"""
Fake tool implementations for the PerformMax AI agent.

Each tool has:
1. A JSON schema definition (sent to Claude so it knows how/when to call it)
2. A fake implementation that simulates a real backend service
"""

import json
import random
import uuid
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# Tool schemas (sent to Claude)
# ─────────────────────────────────────────────

TOOLS = [
    {
        "name": "register_or_login_user",
        "description": (
            "Register a new user account or authenticate an existing user on the "
            "PerformMax platform. Use this when the user wants to sign up, create "
            "an account, login, or access their existing account."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["register", "login"],
                    "description": "Whether to register a new account or login to an existing one.",
                },
                "email": {
                    "type": "string",
                    "description": "The user's email address.",
                },
                "password": {
                    "type": "string",
                    "description": "The user's password.",
                },
                "full_name": {
                    "type": "string",
                    "description": "User's full name. Required only for registration.",
                },
            },
            "required": ["action", "email", "password"],
        },
    },
    {
        "name": "process_payment",
        "description": (
            "Process a subscription payment for a PerformMax plan. "
            "Use this when the user wants to subscribe, upgrade, or purchase a plan. "
            "Always ensure the user is logged in (has a user_id) before calling this."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user's ID obtained after login or registration.",
                },
                "plan": {
                    "type": "string",
                    "enum": ["starter", "professional", "enterprise"],
                    "description": (
                        "Subscription plan: "
                        "starter ($49/mo), professional ($149/mo), enterprise ($499/mo)."
                    ),
                },
                "billing_period": {
                    "type": "string",
                    "enum": ["monthly", "annual"],
                    "description": "Billing period. Annual saves ~20%.",
                },
                "payment_method": {
                    "type": "string",
                    "enum": ["credit_card", "paypal", "bank_transfer"],
                    "description": "Payment method to charge.",
                },
            },
            "required": ["user_id", "plan", "billing_period", "payment_method"],
        },
    },
    {
        "name": "get_marketing_recommendations",
        "description": (
            "Retrieve AI-powered, data-driven performance marketing recommendations "
            "via the PerformMax RAG service. The service retrieves relevant benchmarks, "
            "best practices, and historical patterns to generate personalised insights "
            "on ad-spend optimisation, audience targeting, conversion improvement, and ROI. "
            "Use this when the user asks for advice, tips, or a strategy review."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user's ID.",
                },
                "campaign_type": {
                    "type": "string",
                    "enum": ["search", "display", "social", "video", "email"],
                    "description": "The type of marketing campaign to analyse.",
                },
                "budget": {
                    "type": "number",
                    "description": "Monthly campaign budget in USD.",
                },
                "goals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "List of marketing goals, e.g. "
                        "['increase_conversions', 'reduce_cac', 'improve_roas', 'grow_awareness']."
                    ),
                },
                "current_roas": {
                    "type": "number",
                    "description": "Current Return on Ad Spend, if known (optional).",
                },
            },
            "required": ["user_id", "campaign_type", "budget", "goals"],
        },
    },
]


# ─────────────────────────────────────────────
# Fake service implementations
# ─────────────────────────────────────────────

def _register_or_login_user(
    action: str,
    email: str,
    password: str,
    full_name: str | None = None,
) -> dict:
    """Fake authentication service."""
    user_id = f"usr_{uuid.uuid4().hex[:10]}"
    token = f"tok_{uuid.uuid4().hex}"

    if action == "register":
        name = full_name or email.split("@")[0].replace(".", " ").title()
        return {
            "success": True,
            "action": "registered",
            "user_id": user_id,
            "email": email,
            "full_name": name,
            "token": token,
            "message": f"Account created for {email}. Welcome to PerformMax, {name}!",
            "onboarding_url": "https://app.performmax.io/onboarding",
        }
    else:
        return {
            "success": True,
            "action": "logged_in",
            "user_id": user_id,
            "email": email,
            "token": token,
            "message": f"Logged in successfully as {email}.",
            "last_login": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat() + "Z",
        }


def _plan_features(plan: str) -> list[str]:
    return {
        "starter": [
            "Up to 5 active campaigns",
            "Core analytics dashboard",
            "Email support (48h SLA)",
            "1 user seat",
        ],
        "professional": [
            "Up to 25 active campaigns",
            "Advanced analytics & custom reports",
            "A/B testing suite",
            "Priority support (8h SLA)",
            "5 user seats",
            "REST API access",
        ],
        "enterprise": [
            "Unlimited campaigns",
            "Custom analytics & white-labelling",
            "Dedicated account manager",
            "24/7 phone & chat support",
            "Unlimited user seats",
            "Custom integrations & SSO",
        ],
    }.get(plan, [])


def _process_payment(
    user_id: str,
    plan: str,
    billing_period: str,
    payment_method: str,
) -> dict:
    """Fake payment service."""
    pricing = {
        "starter":      {"monthly": 49,  "annual": 470},
        "professional": {"monthly": 149, "annual": 1430},
        "enterprise":   {"monthly": 499, "annual": 4790},
    }
    amount = pricing[plan][billing_period]
    next_billing = (datetime.utcnow() + timedelta(days=30 if billing_period == "monthly" else 365))

    return {
        "success": True,
        "transaction_id": f"txn_{uuid.uuid4().hex[:14]}",
        "user_id": user_id,
        "plan": plan,
        "billing_period": billing_period,
        "amount_usd": amount,
        "payment_method": payment_method,
        "next_billing_date": next_billing.strftime("%Y-%m-%d"),
        "message": (
            f"Payment of ${amount} USD processed successfully. "
            f"You are now on the {plan.capitalize()} plan ({billing_period} billing)."
        ),
        "features_unlocked": _plan_features(plan),
        "invoice_url": f"https://billing.performmax.io/invoices/{uuid.uuid4().hex[:8]}",
    }


def _get_marketing_recommendations(
    user_id: str,
    campaign_type: str,
    budget: float,
    goals: list[str],
    current_roas: float | None = None,
) -> dict:
    """
    Fake RAG service.

    In a real implementation this would:
      1. Embed the query context (campaign type, goals, budget range).
      2. Retrieve semantically similar past campaigns / benchmarks from a vector DB.
      3. Pass retrieved context + user query to a generation model.
    Here we return realistic-looking static data keyed by campaign type.
    """
    roas = current_roas or round(random.uniform(1.8, 5.0), 2)
    target_roas = round(roas * 1.3, 2)

    playbooks: dict[str, dict] = {
        "search": {
            "quick_wins": [
                "Add negative keywords to eliminate irrelevant traffic (est. 15–20 % spend savings).",
                "Switch to Target CPA or Maximize Conversions bidding aligned with your goals.",
                "Implement ad scheduling — pause spend during hours with <0.5 % conversion rate.",
            ],
            "strategy": (
                "Prioritise long-tail, high-intent keywords. "
                "Broad-match terms are likely inflating CPC without proportional conversion gains."
            ),
            "budget_split": {"brand": "20 %", "competitor": "15 %", "non-brand": "65 %"},
        },
        "social": {
            "quick_wins": [
                "Create 1 % lookalike audiences from your top-converting customers.",
                "Test 15-second video creatives — CPM is typically 30 % lower than static on Meta.",
                "Set a 72-hour retargeting window for cart/page abandoners.",
            ],
            "strategy": (
                "Run awareness campaigns first to seed retargeting pools "
                "before pushing conversion-focused ad sets."
            ),
            "budget_split": {"awareness": "40 %", "consideration": "35 %", "conversion": "25 %"},
        },
        "display": {
            "quick_wins": [
                "Exclude placements with >15 % of spend and <0.1 % CTR.",
                "Enable responsive display ads to maximise inventory coverage.",
                "Cap frequency at 3–5 impressions per user per week to avoid ad fatigue.",
            ],
            "strategy": (
                "Display excels at brand recall, not direct response. "
                "Shift conversion KPIs to assisted metrics rather than last-click."
            ),
            "budget_split": {"prospecting": "60 %", "retargeting": "40 %"},
        },
        "email": {
            "quick_wins": [
                "Segment your list by engagement tier (active / dormant / at-risk).",
                "A/B test subject lines on 20 % of the list before full send.",
                "Launch an automated welcome sequence (Day 0 / 3 / 7) for new subscribers.",
            ],
            "strategy": (
                "Focus on list hygiene and deliverability before scaling volume. "
                "A clean list of 10k outperforms a dirty list of 100k."
            ),
            "budget_split": {"acquisition": "30 %", "nurture": "50 %", "retention": "20 %"},
        },
        "video": {
            "quick_wins": [
                "Hook viewers within the first 5 seconds to reduce skip rate below 30 %.",
                "Add closed captions — 85 % of videos are viewed without sound.",
                "Produce 15-second cut-downs for higher completion rates and cheaper CPVs.",
            ],
            "strategy": (
                "Use video for top-of-funnel awareness. "
                "Pair with search retargeting to capture users who watched but didn't convert."
            ),
            "budget_split": {"YouTube": "50 %", "Meta Reels": "30 %", "TikTok": "20 %"},
        },
    }

    playbook = playbooks.get(campaign_type, playbooks["search"])

    goal_insights: list[str] = []
    for goal in goals:
        if "conversion" in goal:
            goal_insights.append(
                "Landing page speed: ensure <3 s load time and mobile-first layout."
            )
        if "cac" in goal or "cost" in goal:
            goal_insights.append(
                "Audit your attribution model — last-click undervalues awareness channels."
            )
        if "roas" in goal:
            goal_insights.append(
                f"With a ${budget:,.0f} monthly budget, a realistic 30-day ROAS target is {target_roas}x."
            )
        if "awareness" in goal:
            goal_insights.append(
                "Track Brand Search Lift and Direct traffic alongside impressions for awareness measurement."
            )

    return {
        "user_id": user_id,
        "campaign_type": campaign_type,
        "rag_sources_retrieved": 12,  # simulates RAG retrieval count
        "current_roas": roas,
        "target_roas_30d": target_roas,
        "estimated_budget_efficiency": f"{random.randint(62, 88)} %",
        "quick_wins": playbook["quick_wins"],
        "strategy_overview": playbook["strategy"],
        "recommended_budget_split": playbook["budget_split"],
        "goal_specific_insights": (
            goal_insights or ["Set up conversion tracking to unlock deeper goal-specific insights."]
        ),
        "industry_benchmarks": {
            "avg_roas": 3.2,
            "top_decile_roas": 6.8,
            "your_roas": roas,
        },
        "next_steps": [
            "Pick the highest-impact quick win and implement it this week.",
            "Verify conversion tracking covers all key actions (purchase, lead, sign-up).",
            "Schedule a 2-week A/B test to validate the recommended change.",
        ],
        "data_sources": [
            "PerformMax benchmark database — Q4 2024",
            "Platform best-practice corpus (Google, Meta, TikTok docs)",
            "Anonymised performance data from 4,200 similar accounts",
        ],
    }


# ─────────────────────────────────────────────
# Dispatcher used by the agent loop
# ─────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name and return a JSON string result."""
    if tool_name == "register_or_login_user":
        result = _register_or_login_user(**tool_input)
    elif tool_name == "process_payment":
        result = _process_payment(**tool_input)
    elif tool_name == "get_marketing_recommendations":
        result = _get_marketing_recommendations(**tool_input)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}

    return json.dumps(result, indent=2)
