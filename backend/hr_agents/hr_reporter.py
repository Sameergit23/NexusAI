"""
hr_reporter.py
NexusAI HR Onboarding — HR Reporter Agent

Responsibility:
  1. Compute onboarding KPIs (readiness %, hours saved, cost saved).
  2. Persist them via db.save_analytics() and mark the run completed.
  3. Return the report in the shape the dashboard renders
     (docs/hr-onboarding/OVERVIEW.md).
"""

from __future__ import annotations

from backend import db

# Locked impact constants — do NOT change (docs/hr-onboarding/OVERVIEW.md)
HOURS_SAVED_PER_HIRE = 6      # avg manual time saved per hire (HR + manager)
COST_INR_PER_HOUR = 1500      # blended HR + manager cost


async def run(run_id: str, tasks_total: int, tasks_completed: int, total_hires: int) -> dict:
    await db.log(run_id, "hr_reporter", "Computing onboarding readiness report...")

    readiness_pct = (tasks_completed / tasks_total * 100) if tasks_total else 0
    hours_saved = total_hires * HOURS_SAVED_PER_HIRE
    cost_saved = hours_saved * COST_INR_PER_HOUR

    report = {
        "total_hires": total_hires,
        "tasks_completed": tasks_completed,
        "tasks_total": tasks_total,
        "readiness_pct": round(readiness_pct, 2),
        "hours_saved": hours_saved,
        "cost_saved_inr": cost_saved,
        "emails_sent": (db.ctx_get(run_id, "notifications") or {}).get("sent", 0),
    }

    db.save_analytics(run_id, report)
    db.set_run_status(run_id, "completed")

    await db.log(
        run_id,
        "hr_reporter",
        f"KPIs saved: {total_hires} hires {report['readiness_pct']}% ready, "
        f"{hours_saved} h saved (Rs {cost_saved:,})",
    )
    await db.log(run_id, "hr_reporter", "Run marked completed")

    return report
