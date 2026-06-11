"""All 4 tool handlers — the bridge between Claude's tool calls and the agents.

Each handler:
  - takes a single `args` dict (Claude's tool input + an injected `run_id`),
  - reads canonical data from the shared run context (db.ctx_*),
  - calls the matching agent, stores the result back in the context,
  - returns a plain dict.
"""

from backend import db
from backend.agents import planner, route_optimizer, notification, analytics


async def handle_plan_tasks(args: dict) -> dict:
    run_id = args["run_id"]
    goal = args.get("goal") or db.ctx_get(run_id, "goal")
    deliveries = db.ctx_get(run_id, "deliveries") or args.get("deliveries") or []
    num_vehicles = db.ctx_get(run_id, "num_vehicles") or args.get("num_vehicles") or 1
    result = await planner.run(goal, deliveries, num_vehicles, run_id)
    db.ctx_set(run_id, "zones", result.get("zones", []))
    return result


async def handle_optimise_routes(args: dict) -> dict:
    run_id = args["run_id"]
    zones = db.ctx_get(run_id, "zones") or args.get("zones") or []
    result = await route_optimizer.run(run_id, zones)
    db.ctx_set(run_id, "routes", result)
    db.ctx_set(run_id, "naive_km", result.get("naive_km"))
    db.ctx_set(run_id, "optimised_km", result.get("optimised_km"))
    return result


async def handle_send_notifications(args: dict) -> dict:
    run_id = args["run_id"]
    routes = args.get("routes") or db.ctx_get(run_id, "routes")
    deliveries = db.ctx_get(run_id, "deliveries") or args.get("deliveries") or []
    result = await notification.run(run_id, routes, deliveries)
    db.ctx_set(run_id, "notifications", result)
    return result


async def handle_generate_report(args: dict) -> dict:
    run_id = args["run_id"]
    naive_km = args.get("naive_km")
    if naive_km is None:
        naive_km = db.ctx_get(run_id, "naive_km", 0)
    optimised_km = args.get("optimised_km")
    if optimised_km is None:
        optimised_km = db.ctx_get(run_id, "optimised_km", 0)
    deliveries = db.ctx_get(run_id, "deliveries") or []
    total = len(deliveries) or args.get("deliveries_total", 0)
    on_time = args.get("deliveries_on_time", total)
    result = await analytics.run(run_id, naive_km, optimised_km, total, on_time)
    db.ctx_set(run_id, "report", result)
    return result
