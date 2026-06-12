"""
hr_reporter.py
NexusAI HR Onboarding — HR Reporter Agent

Responsibility:
  1. Collect KPI data from shared context (set by hr_communicator + hr_planner).
  2. Persist KPIs via db.save_analytics() using locked constant keys.
  3. Return a human-readable onboarding summary report.
  4. Fall back to simulation mode — no external API key required.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Locked KPI constant keys — do NOT rename; orchestrator + dashboard depend on these
# ---------------------------------------------------------------------------

KPI_TOTAL_HIRES: str = "hr_total_hires"
KPI_EMAILS_SENT: str = "hr_emails_sent"
KPI_EMAILS_SIMULATED: str = "hr_emails_simulated"
KPI_TASKS_SCHEDULED: str = "hr_tasks_scheduled"
KPI_ONBOARDING_SUCCESS_RATE: str = "hr_onboarding_success_rate"
KPI_REPORT_GENERATED_AT: str = "hr_report_generated_at"


# ---------------------------------------------------------------------------
# KPI collector — reads from shared context
# ---------------------------------------------------------------------------

def _collect_kpis(db: Any, hire: dict[str, Any]) -> dict[str, Any]:
    """
    Pull data written by hr_communicator and hr_planner from shared context,
    then compute derived KPIs.
    """
    communicator_result: dict[str, Any] = db.ctx_get("hr_communicator_result") or {}
    planner_result: dict[str, Any] = db.ctx_get("hr_planner_result") or {}

    # Raw signals
    email_sent: bool = communicator_result.get("email_status") in ("sent", "simulated")
    email_simulated: bool = communicator_result.get("simulated", True)
    tasks_scheduled: int = planner_result.get("tasks_scheduled", 0)

    # Derived
    success: bool = email_sent  # extend with more criteria as feature grows
    success_rate: float = 1.0 if success else 0.0

    return {
        KPI_TOTAL_HIRES: 1,
        KPI_EMAILS_SENT: 1 if email_sent else 0,
        KPI_EMAILS_SIMULATED: 1 if email_simulated else 0,
        KPI_TASKS_SCHEDULED: tasks_scheduled,
        KPI_ONBOARDING_SUCCESS_RATE: success_rate,
        KPI_REPORT_GENERATED_AT: datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def _build_report(hire: dict[str, Any], kpis: dict[str, Any]) -> str:
    """Compose a plain-text onboarding summary report."""
    name = hire.get("name", "New Hire")
    role = hire.get("role", "N/A")
    start_date = hire.get("start_date", "N/A")
    team = hire.get("team", "N/A")

    email_status = "[OK] Sent" if kpis[KPI_EMAILS_SENT] else "[--] Not sent"
    if kpis[KPI_EMAILS_SIMULATED]:
        email_status += " (simulated)"

    tasks = kpis[KPI_TASKS_SCHEDULED]
    success_pct = int(kpis[KPI_ONBOARDING_SUCCESS_RATE] * 100)
    generated_at = kpis[KPI_REPORT_GENERATED_AT]

    sep = "=" * 43
    div = "-" * 43
    return (
        sep + "\n"
        + "    NexusAI HR Onboarding Summary Report\n"
        + sep + "\n"
        + f"  Hire name   : {name}\n"
        + f"  Role        : {role}\n"
        + f"  Start date  : {start_date}\n"
        + f"  Team        : {team}\n"
        + div + "\n"
        + f"  Welcome email : {email_status}\n"
        + f"  Tasks queued  : {tasks}\n"
        + f"  Success rate  : {success_pct}%\n"
        + div + "\n"
        + f"  Generated at  : {generated_at}\n"
        + sep + "\n"
    )


# ---------------------------------------------------------------------------
# Public agent entry-point
# ---------------------------------------------------------------------------

async def run_hr_reporter(
    db: Any,
    hire: dict[str, Any],
) -> dict[str, Any]:
    """
    Main entry-point called by the orchestrator / handler.

    Args:
        db:   Database/context object (ctx_get, log, save_analytics).
        hire: Dict with keys: name, role, start_date, team, email.

    Returns:
        Result dict with keys: agent, status, kpis, report.
    """
    await db.log("hr_reporter", "start", {"hire_name": hire.get("name")})

    # 1. Collect KPIs from shared context
    kpis: dict[str, Any] = _collect_kpis(db, hire)

    # 2. Persist KPIs
    await db.save_analytics(kpis)

    # 3. Build human-readable report
    report: str = _build_report(hire, kpis)

    # 4. Store in context for downstream use (e.g., orchestrator response)
    db.ctx_set("hr_reporter_result", {
        "kpis": kpis,
        "report_preview": report[:200],
    })

    result: dict[str, Any] = {
        "agent": "hr_reporter",
        "status": "ok",
        "kpis": kpis,
        "report": report,
    }

    await db.log("hr_reporter", "done", result)
    return result
