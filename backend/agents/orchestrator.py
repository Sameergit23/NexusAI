"""Orchestrator agent — the brain.

Runs a genuine Claude tool-use loop: reason → call an agent → evaluate the
result → call the next → continue until Claude verifies the goal is complete.
Implements the 6 agentic principles (goal-directed, multi-agent, real tool use,
reasoning, autonomous failure recovery, self-verification).

If no ANTHROPIC_API_KEY is configured, a deterministic fallback runs the same
agents in order so the data pipeline still works (useful for local testing).
"""
from __future__ import annotations

import asyncio
import json
import os

from backend import db
from backend.tools import handlers
from backend.tools.definitions import ALL_TOOLS

MODEL = "claude-sonnet-4-6"
MAX_STEPS = 10

SYSTEM_PROMPT = """You are the Orchestrator of NexusAI, an autonomous multi-agent system for delivery operations.

You coordinate four specialist agents, available to you as tools:
- plan_tasks: groups the deliveries into geographic zones (call this FIRST).
- optimise_routes: computes the optimal real road route for each zone (call AFTER planning).
- send_notifications: sends ETA messages to every recipient (call AFTER routing).
- generate_report: computes the final impact report — distance, CO2, cost, time saved (call LAST).

How to operate:
1. Reason about what the goal needs and what to do next.
2. Call the right tool with the right inputs.
3. Evaluate each result. If a tool returns an error, decide how to recover (retry, or adjust and continue) — never give up and never ask the human.
4. Continue until the goal is fully achieved, then stop and give a one-paragraph summary of the outcome.

You are fully autonomous. Do not ask the user any questions."""

TOOL_MAP = {
    "plan_tasks": handlers.handle_plan_tasks,
    "optimise_routes": handlers.handle_optimise_routes,
    "send_notifications": handlers.handle_send_notifications,
    "generate_report": handlers.handle_generate_report,
}


async def run(goal: str, deliveries: list, num_vehicles: int) -> dict:
    """Create a run and execute it (synchronous helper / direct use)."""
    run_id = db.create_run(goal, num_vehicles)
    db.ctx_set(run_id, "goal", goal)
    db.ctx_set(run_id, "deliveries", deliveries)
    db.ctx_set(run_id, "num_vehicles", num_vehicles)
    return await _execute(run_id)


async def run_existing(run_id: str) -> dict:
    """Execute a run whose record + context were already created (background use)."""
    return await _execute(run_id)


async def _execute(run_id: str) -> dict:
    goal = db.ctx_get(run_id, "goal")
    db.log(run_id, "orchestrator", f"Goal received: {goal}")
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            db.log(run_id, "orchestrator",
                   "No ANTHROPIC_API_KEY - running deterministic pipeline", "warning")
            return await _fallback(run_id)
        return await _agentic_loop(run_id, api_key)
    except Exception as e:
        err = str(e)
        # If Claude is unavailable (billing, rate limit, network), fall back gracefully.
        db.log(run_id, "orchestrator", f"Claude unavailable ({err[:120]}) - switching to deterministic pipeline", "warning")
        return await _fallback(run_id)


async def _agentic_loop(run_id: str, api_key: str) -> dict:
    import anthropic

    ai = anthropic.Anthropic(api_key=api_key)
    goal = db.ctx_get(run_id, "goal")
    deliveries = db.ctx_get(run_id, "deliveries")
    num_vehicles = db.ctx_get(run_id, "num_vehicles", 1)

    messages = [{
        "role": "user",
        "content": json.dumps({"goal": goal, "deliveries": deliveries, "num_vehicles": num_vehicles}),
    }]

    for _ in range(MAX_STEPS):
        resp = await asyncio.to_thread(
            ai.messages.create,
            model=MODEL, max_tokens=4096,
            system=SYSTEM_PROMPT, tools=ALL_TOOLS, messages=messages,
        )

        if resp.stop_reason != "tool_use":          # self-verification: Claude is done
            summary = _final_text(resp)
            if summary:
                db.log(run_id, "orchestrator", summary)
            db.log(run_id, "orchestrator", "Goal verified complete")
            break

        messages.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            db.log(run_id, "orchestrator", f"Reasoning -> calling {block.name}")
            try:                                     # autonomous failure recovery
                args = dict(block.input or {})
                args["run_id"] = run_id
                result = await TOOL_MAP[block.name](args)
            except Exception as e:
                db.log(run_id, "orchestrator", f"{block.name} failed: {e}", "error")
                result = {"error": str(e)}
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(_summarise(result))[:6000],
            })
        messages.append({"role": "user", "content": tool_results})

    db.set_run_status(run_id, "completed")
    return _result(run_id)


async def _fallback(run_id: str) -> dict:
    """Deterministic pipeline when Claude is unavailable. NOT the agentic path —
    it just guarantees the data flow works end-to-end for local testing."""
    await handlers.handle_plan_tasks({"run_id": run_id})
    await handlers.handle_optimise_routes({"run_id": run_id})
    await handlers.handle_send_notifications({"run_id": run_id})
    await handlers.handle_generate_report({"run_id": run_id})
    db.set_run_status(run_id, "completed")
    db.log(run_id, "orchestrator", "Goal verified complete (fallback)")
    return _result(run_id)


def _summarise(result):
    """Strip heavy geometry before sending a result back to Claude (saves tokens)."""
    if not isinstance(result, dict):
        return result
    out = {}
    for k, v in result.items():
        if isinstance(v, dict) and "geometry" in v:
            out[k] = {kk: vv for kk, vv in v.items() if kk != "geometry"}
        else:
            out[k] = v
    return out


def _final_text(resp) -> str:
    parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
    return " ".join(p.strip() for p in parts if p).strip()


def _result(run_id: str) -> dict:
    return {
        "run_id": run_id,
        "report": db.ctx_get(run_id, "report"),
        "routes": db.ctx_get(run_id, "routes"),
        "notifications": db.ctx_get(run_id, "notifications"),
    }
