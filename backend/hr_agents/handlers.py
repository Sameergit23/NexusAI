from backend import db

from backend.hr_agents.hr_planner import run as planner_run
from backend.hr_agents.onboarding_scheduler import run as scheduler_run


async def handle_hr_plan(args):

    run_id = args["run_id"]

    goal = db.ctx_get(
        run_id,
        "goal"
    )

    employees = db.ctx_get(
        run_id,
        "employees"
    )

    return await planner_run(
        goal,
        employees,
        run_id
    )


async def handle_onboarding_schedule(args):

    run_id = args["run_id"]

    planner_result = db.ctx_get(
        run_id,
        "planner_result"
    )

    return await scheduler_run(
        run_id,
        planner_result["plan"]
    )