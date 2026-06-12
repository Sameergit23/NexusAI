"""Integration check for the HR vertical (orchestrator routing + /run contract).

Run with NO api keys:
    PYTHONPATH=. python backend/test_hr_routing.py

What it does:
- if backend/hr_agents is merged -> runs the real HR fallback pipeline end-to-end
  and checks the report shape against docs/hr-onboarding/OVERVIEW.md
- if not merged yet -> stubs the four handlers to verify the orchestrator
  routes the hr vertical correctly, and that a missing hr_agents fails the
  run gracefully instead of crashing the server
- always -> logistics fallback regression (the Round 1 demo must keep working)
"""
import asyncio
import json
import os
import sys
import types

os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("RESEND_API_KEY", None)

from backend import db
from backend.agents import orchestrator

EMPLOYEES = [
    {"id": "1", "name": "Priya", "role": "Backend Engineer", "team": "Platform", "email": "p@x.com"},
    {"id": "2", "name": "Arjun", "role": "Frontend Engineer", "team": "Web", "email": "a@x.com"},
]

REPORT_KEYS = {
    "total_hires", "tasks_completed", "tasks_total",
    "readiness_pct", "hours_saved", "cost_saved_inr", "emails_sent",
}


def make_hr_run() -> str:
    run_id = db.create_run("Onboard 2 engineers joining Monday", 0)
    db.ctx_set(run_id, "vertical", "hr")
    db.ctx_set(run_id, "goal", "Onboard 2 engineers joining Monday")
    db.ctx_set(run_id, "employees", EMPLOYEES)
    return run_id


def hr_agents_available() -> bool:
    try:
        from backend.hr_agents import handlers  # noqa: F401
        return True
    except ImportError:
        return False


def install_stub_handlers(calls: list) -> None:
    """Stand-in hr_agents so routing is testable before the real ones merge."""
    def mk(name, ctx_key=None, value=None):
        async def h(args):
            calls.append(name)
            if ctx_key:
                db.ctx_set(args["run_id"], ctx_key, value)
            return {"ok": name}
        return h

    pkg = types.ModuleType("backend.hr_agents")
    mod = types.ModuleType("backend.hr_agents.handlers")
    mod.handle_plan_onboarding = mk("plan_onboarding", "tasks_total", 14)
    mod.handle_book_meetings = mk("book_meetings", "meetings", {"total_meetings": 6})
    mod.handle_send_welcome_emails = mk("send_welcome_emails", "notifications", {"sent": 2, "failed": 0, "simulated": True})
    mod.handle_hr_report = mk("hr_report", "report", {k: 0 for k in REPORT_KEYS})
    pkg.handlers = mod
    sys.modules["backend.hr_agents"] = pkg
    sys.modules["backend.hr_agents.handlers"] = mod


async def main():
    real = hr_agents_available()

    if not real:
        # graceful failure path: hr run must fail, not crash
        rid = make_hr_run()
        await orchestrator.run_existing(rid)
        status = db.get_run(rid)["run"]["status"]
        assert status == "failed", f"expected failed, got {status}"
        print("PASS: missing hr_agents -> hr run failed gracefully")

        calls = []
        install_stub_handlers(calls)
        rid = make_hr_run()
        await orchestrator.run_existing(rid)
        assert calls == ["plan_onboarding", "book_meetings", "send_welcome_emails", "hr_report"], calls
        assert db.get_run(rid)["run"]["status"] == "completed"
        print("PASS: hr fallback called all 4 tools in order (stubbed handlers)")
    else:
        rid = make_hr_run()
        await orchestrator.run_existing(rid)
        run = db.get_run(rid)
        assert run["run"]["status"] == "completed", run["run"]["status"]
        report = run["report"] or {}
        missing = REPORT_KEYS - set(report)
        assert not missing, f"report missing keys: {missing}"
        assert report["total_hires"] == len(EMPLOYEES), report
        print("PASS: real hr pipeline completed, report matches OVERVIEW contract")
        print(json.dumps(report, indent=2, default=str))

    # logistics regression — Round 1 demo must keep working
    rid = db.create_run("Deliver 3 packages", 1)
    db.ctx_set(rid, "goal", "Deliver 3 packages")
    db.ctx_set(rid, "deliveries", [
        {"id": "1", "address": "MG Road, Bengaluru", "lat": 12.9758, "lng": 77.6045},
        {"id": "2", "address": "Indiranagar, Bengaluru", "lat": 12.9719, "lng": 77.6412},
        {"id": "3", "address": "Koramangala, Bengaluru", "lat": 12.9352, "lng": 77.6245},
    ])
    db.ctx_set(rid, "num_vehicles", 1)
    await orchestrator.run_existing(rid)
    run = db.get_run(rid)
    assert run["run"]["status"] == "completed", run["run"]["status"]
    assert run["report"], "logistics report missing"
    print("PASS: logistics fallback still completes with a report")

    print("\nALL CHECKS PASSED" + (" (real hr_agents)" if real else " (hr_agents not merged yet — stub mode)"))


asyncio.run(main())
