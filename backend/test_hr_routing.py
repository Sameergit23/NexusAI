"""Integration check for the HR vertical (orchestrator routing + /run contract).

Run with NO api keys:
    PYTHONPATH=. python backend/test_hr_routing.py

Adapts to the state of backend/hr_agents:
- missing entirely  -> graceful-failure check, then full-stub pipeline check
- partially merged  -> graceful-failure check, then hybrid run (real handlers
  where they exist, stubs for the rest) so the merged half is exercised
  through the orchestrator
- complete          -> real pipeline end-to-end, report checked against
  docs/hr-onboarding/OVERVIEW.md
Always finishes with the logistics fallback regression (Round 1 must work).
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

HANDLER_NAMES = [
    "handle_plan_onboarding",
    "handle_book_meetings",
    "handle_send_welcome_emails",
    "handle_hr_report",
]

REPORT_KEYS = {
    "total_hires", "tasks_completed", "tasks_total",
    "readiness_pct", "hours_saved", "cost_saved_inr", "emails_sent",
}


def make_hr_run() -> str:
    run_id = db.create_run("Onboard 2 engineers joining Monday", 0, vertical="hr")
    db.ctx_set(run_id, "vertical", "hr")
    db.ctx_set(run_id, "goal", "Onboard 2 engineers joining Monday")
    db.ctx_set(run_id, "employees", EMPLOYEES)
    return run_id


def real_handlers():
    """The real handlers module, or None if backend/hr_agents isn't merged."""
    try:
        from backend.hr_agents import handlers
        return handlers
    except ImportError:
        return None


def stub(name, ctx_key=None, value=None):
    async def h(args):
        if ctx_key:
            db.ctx_set(args["run_id"], ctx_key, value)
        return {"ok": name}
    return h


async def stub_report(args):
    """Reporter stub: computes from ctx exactly like the real one will,
    so hybrid runs validate that upstream handlers fed the context."""
    rid = args["run_id"]
    total = db.ctx_get(rid, "tasks_total", 0)
    hires = len(db.ctx_get(rid, "employees") or [])
    report = {
        "total_hires": hires,
        "tasks_completed": total,
        "tasks_total": total,
        "readiness_pct": 100 if total else 0,
        "hours_saved": hires * 6,
        "cost_saved_inr": hires * 6 * 1500,
        "emails_sent": (db.ctx_get(rid, "notifications") or {}).get("sent", 0),
    }
    db.ctx_set(rid, "report", report)
    return report


def install_handlers(real) -> list:
    """Put a handlers module in sys.modules: real functions where they exist,
    stubs elsewhere. Returns the list of stubbed names."""
    stubs = {
        "handle_plan_onboarding": stub("plan_onboarding", "tasks_total", 14),
        "handle_book_meetings": stub("book_meetings", "meetings", {"total_meetings": 6}),
        "handle_send_welcome_emails": stub("send_welcome_emails", "notifications", {"sent": 2, "failed": 0, "simulated": True}),
        "handle_hr_report": stub_report,
    }
    pkg = types.ModuleType("backend.hr_agents")
    mod = types.ModuleType("backend.hr_agents.handlers")
    stubbed = []
    for name in HANDLER_NAMES:
        fn = getattr(real, name, None)
        if fn is None:
            fn = stubs[name]
            stubbed.append(name)
        setattr(mod, name, fn)
    pkg.handlers = mod
    sys.modules["backend.hr_agents"] = pkg
    sys.modules["backend.hr_agents.handlers"] = mod
    return stubbed


async def main():
    real = real_handlers()
    missing = HANDLER_NAMES if real is None else [n for n in HANDLER_NAMES if not hasattr(real, n)]

    if missing:
        # 1. graceful failure: incomplete hr_agents must fail the run, not hang it
        rid = make_hr_run()
        await orchestrator.run_existing(rid)
        status = db.get_run(rid)["run"]["status"]
        assert status == "failed", f"expected failed, got {status}"
        print(f"PASS: incomplete hr_agents (missing {len(missing)}) -> run failed gracefully")

        # 2. fill the gaps with stubs and run the pipeline through the orchestrator
        stubbed = install_handlers(real)
        rid = make_hr_run()
        await orchestrator.run_existing(rid)
        run = db.get_run(rid)
        assert run["run"]["status"] == "completed", run["run"]["status"]
        report = run["report"] or {}
        assert REPORT_KEYS <= set(report), f"report missing keys: {REPORT_KEYS - set(report)}"
        if "handle_plan_onboarding" not in stubbed:
            assert report["tasks_total"] > 0, "real planner did not feed tasks_total into ctx"
        print(f"PASS: hybrid hr pipeline completed (stubbed: {stubbed or 'none'})")
        print(json.dumps(report, indent=2, default=str))
    else:
        rid = make_hr_run()
        await orchestrator.run_existing(rid)
        run = db.get_run(rid)
        assert run["run"]["status"] == "completed", run["run"]["status"]
        report = run["report"] or {}
        assert REPORT_KEYS <= set(report), f"report missing keys: {REPORT_KEYS - set(report)}"
        assert report["total_hires"] == len(EMPLOYEES), report
        assert report["tasks_total"] > 0, report
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

    state = "complete" if not missing else f"missing {missing}"
    print(f"\nALL CHECKS PASSED (hr_agents: {state})")


asyncio.run(main())
