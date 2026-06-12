"""Shared run store + per-run working context for NexusAI.

Lean mode: in-memory (zero setup — the whole system runs with only an
ANTHROPIC_API_KEY, or with no keys at all in deterministic fallback mode).

To switch to Supabase later, replace the bodies of the helper functions below
with supabase-py calls (see docs/supabase_schema.sql for the table shapes).
The function signatures stay the same, so no agent code has to change.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

# ── In-memory "tables" ───────────────────────────────────────────────
_runs: dict[str, dict] = {}        # run_id -> run record
_logs: dict[str, list] = {}        # run_id -> [log records]
_deliveries: dict[str, list] = {}  # run_id -> [delivery records]
_analytics: dict[str, dict] = {}   # run_id -> analytics record

# ── Per-run working context (the orchestrator's shared scratchpad) ───
_context: dict[str, dict] = {}     # run_id -> { goal, deliveries, zones, routes, report, ... }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── runs ─────────────────────────────────────────────────────────────
def create_run(goal: str, num_vehicles: int, vertical: str = "logistics") -> str:
    run_id = str(uuid.uuid4())
    _runs[run_id] = {
        "id": run_id,
        "goal": goal,
        "num_vehicles": num_vehicles,
        "vertical": vertical,
        "status": "running",
        "created_at": _now(),
        "completed_at": None,
    }
    _logs[run_id] = []
    _deliveries[run_id] = []
    _context[run_id] = {}
    return run_id


def set_run_status(run_id: str, status: str) -> None:
    run = _runs.get(run_id)
    if not run:
        return
    run["status"] = status
    if status in ("completed", "failed"):
        run["completed_at"] = _now()


def list_runs() -> list:
    return sorted(_runs.values(), key=lambda r: r["created_at"], reverse=True)


# ── agent_logs ───────────────────────────────────────────────────────
async def log(run_id: str, agent: str, message: str, level: str = "info") -> None:
    """Async so agents can `await log(...)`. Stays cheap — no I/O is awaited."""
    _logs.setdefault(run_id, []).append(
        {"agent": agent, "message": message, "level": level, "created_at": _now()}
    )
    try:  # console echo must never crash a run (Windows cp1252 etc.)
        print(f"[{agent}] {message}")
    except Exception:
        pass


# ── deliveries / analytics ──────────────────────────────────────────
def save_deliveries(run_id: str, rows: list) -> None:
    _deliveries.setdefault(run_id, []).extend(rows)


def save_analytics(run_id: str, data: dict) -> None:
    _analytics[run_id] = {**data, "run_id": run_id, "created_at": _now()}


# ── read (what the frontend polls) ──────────────────────────────────
def get_run(run_id: str) -> dict:
    c = _context.get(run_id, {})
    return {
        "run": _runs.get(run_id),
        "logs": _logs.get(run_id, []),
        "deliveries": _deliveries.get(run_id, []),
        "analytics": _analytics.get(run_id),
        "routes": c.get("routes"),   # includes geometry for the map
        "report": c.get("report"),
    }


# ── working context helpers ─────────────────────────────────────────
def ctx_set(run_id: str, key: str, value) -> None:
    _context.setdefault(run_id, {})[key] = value


def ctx_get(run_id: str, key: str, default=None):
    return _context.get(run_id, {}).get(key, default)
