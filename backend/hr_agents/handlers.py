from backend import db

from backend.hr_agents.hr_planner import run as planner_run
from backend.hr_agents.onboarding_scheduler import run as scheduler_run
from backend.hr_agents.hr_communicator import run as communicator_run
from backend.hr_agents.hr_reporter import run as reporter_run


async def handle_plan_onboarding(args):

    run_id = args["run_id"]

    goal = args.get("goal") or db.ctx_get(run_id, "goal")

    employees = db.ctx_get(run_id, "employees") or []

    result = await planner_run(goal, employees, run_id)

    # shared context keys the scheduler, communicator and reporter read
    db.ctx_set(run_id, "cohorts", result["plan"])
    db.ctx_set(run_id, "tasks_total", result["tasks_total"])

    return result


async def handle_book_meetings(args):

    run_id = args["run_id"]

    cohorts = db.ctx_get(run_id, "cohorts") or []

    result = await scheduler_run(run_id, cohorts)

    db.ctx_set(run_id, "meetings", result)

    return result


async def handle_send_welcome_emails(args):

    run_id = args["run_id"]

    employees = db.ctx_get(run_id, "employees") or []

    meetings = db.ctx_get(run_id, "meetings") or {}

    result = await communicator_run(run_id, employees, meetings)

    db.ctx_set(run_id, "notifications", result)

    return result


async def handle_hr_report(args):

    run_id = args["run_id"]

    tasks_total = db.ctx_get(run_id, "tasks_total", 0)

    # Assume all assigned tasks are completed for the demo
    tasks_completed = tasks_total

    total_hires = len(db.ctx_get(run_id, "employees") or [])

    result = await reporter_run(run_id, tasks_total, tasks_completed, total_hires)

    db.ctx_set(run_id, "report", result)

    return result
