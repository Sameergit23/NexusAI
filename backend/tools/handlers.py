from backend.agents.planner import run as planner_run
from backend.agents.route_optimizer import run as optimizer_run


async def handle_plan_tasks(args):
    return await planner_run(
        args["goal"],
        args["deliveries"],
        args["num_vehicles"],
        args["run_id"]
    )


async def handle_optimise_routes(args):
    return await optimizer_run(
        args["run_id"],
        args["zones"]
    )