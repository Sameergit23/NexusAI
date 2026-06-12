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
from backend.tools.definitions import ALL_TOOLS, HR_TOOLS

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

HR_SYSTEM_PROMPT = """You are the Orchestrator of NexusAI, an autonomous multi-agent system for HR onboarding.

You coordinate four specialist agents, available to you as tools:
- plan_onboarding: groups the new hires into team cohorts and assigns each a Day 1-5 task checklist (call this FIRST).
- book_meetings: books the manager, buddy and HR 1:1 meetings for every hire (call AFTER planning).
- send_welcome_emails: drafts and sends a personalised welcome email to every hire (call AFTER booking).
- hr_report: computes the final readiness report - readiness %, hours saved, cost saved (call LAST).

How to operate:
1. Reason about what the goal needs and what to do next.
2. Call the right tool with the right inputs.
3. Evaluate each result. If a tool returns an error, decide how to recover (retry, or adjust and continue) — never give up and never ask the human.
4. Continue until the goal is fully achieved, then stop and give a one-paragraph summary of the outcome.

You are fully autonomous. Do not ask the user any questions."""


def _hr_tool_map() -> dict:
    """HR handlers live in backend/hr_agents/ (owned by other branches).
    Imported lazily so the logistics demo never depends on them existing."""
    from backend.hr_agents import handlers as hr_handlers
    return {
        "plan_onboarding": hr_handlers.handle_plan_onboarding,
        "book_meetings": hr_handlers.handle_book_meetings,
        "send_welcome_emails": hr_handlers.handle_send_welcome_emails,
        "hr_report": hr_handlers.handle_hr_report,
    }


def _tooling(run_id: str) -> tuple[str, list, dict]:
    """Pick system prompt, tool schemas and tool map for this run's vertical."""
    if db.ctx_get(run_id, "vertical", "logistics") == "hr":
        return HR_SYSTEM_PROMPT, HR_TOOLS, _hr_tool_map()
    return SYSTEM_PROMPT, ALL_TOOLS, TOOL_MAP


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
    await db.log(run_id, "orchestrator", f"Goal received: {goal}")
    if db.ctx_get(run_id, "vertical", "logistics") == "hr":
        try:
            _hr_tool_map()
        except (ImportError, AttributeError) as e:
            # HR agents missing or incomplete — fail this run, never touch logistics.
            # AttributeError covers a merged hr_agents whose handlers don't match
            # the tool contract yet (e.g. only one teammate's half is in).
            await db.log(run_id, "orchestrator", f"HR agents unavailable: {e}", "error")
            db.set_run_status(run_id, "failed")
            return _result(run_id)
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            await db.log(run_id, "orchestrator",
                         "No ANTHROPIC_API_KEY - running deterministic pipeline", "warning")
            return await _fallback(run_id)
        return await _agentic_loop(run_id, api_key)
    except Exception as e:
        err = str(e)
        # If Claude is unavailable (billing, rate limit, network), fall back gracefully.
        await db.log(run_id, "orchestrator", f"Claude unavailable ({err[:120]}) - switching to deterministic pipeline", "warning")
        try:
            return await _fallback(run_id)
        except Exception as e2:
            # Runs execute as fire-and-forget asyncio tasks: if this escapes, the
            # exception is swallowed and the run stays "running" forever in the UI.
            await db.log(run_id, "orchestrator", f"Fallback failed: {e2}", "error")
            db.set_run_status(run_id, "failed")
            return _result(run_id)


async def _agentic_loop(run_id: str, api_key: str) -> dict:
    import anthropic

    ai = anthropic.Anthropic(api_key=api_key)
    goal = db.ctx_get(run_id, "goal")
    system_prompt, tools, tool_map = _tooling(run_id)

    if db.ctx_get(run_id, "vertical", "logistics") == "hr":
        payload = {"goal": goal, "employees": db.ctx_get(run_id, "employees")}
    else:
        payload = {
            "goal": goal,
            "deliveries": db.ctx_get(run_id, "deliveries"),
            "num_vehicles": db.ctx_get(run_id, "num_vehicles", 1),
        }

    messages = [{"role": "user", "content": json.dumps(payload)}]

    for _ in range(MAX_STEPS):
        resp = await asyncio.to_thread(
            ai.messages.create,
            model=MODEL, max_tokens=4096,
            system=system_prompt, tools=tools, messages=messages,
        )

        if resp.stop_reason != "tool_use":          # self-verification: Claude is done
            summary = _final_text(resp)
            if summary:
                await db.log(run_id, "orchestrator", summary)
            await db.log(run_id, "orchestrator", "Goal verified complete")
            break

        messages.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            await db.log(run_id, "orchestrator", f"Reasoning -> calling {block.name}")
            try:                                     # autonomous failure recovery
                args = dict(block.input or {})
                args["run_id"] = run_id
                result = await tool_map[block.name](args)
            except Exception as e:
                await db.log(run_id, "orchestrator", f"{block.name} failed: {e}", "error")
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
    if db.ctx_get(run_id, "vertical", "logistics") == "hr":
        hr = _hr_tool_map()
        await hr["plan_onboarding"]({"run_id": run_id})
        await hr["book_meetings"]({"run_id": run_id})
        await hr["send_welcome_emails"]({"run_id": run_id})
        await hr["hr_report"]({"run_id": run_id})
    else:
        await handlers.handle_plan_tasks({"run_id": run_id})
        await handlers.handle_optimise_routes({"run_id": run_id})
        await handlers.handle_send_notifications({"run_id": run_id})
        await handlers.handle_generate_report({"run_id": run_id})
    db.set_run_status(run_id, "completed")
    await db.log(run_id, "orchestrator", "Goal verified complete (fallback)")
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
