"""NexusAI — FastAPI server.

Endpoints:
  GET  /health        → liveness check
  POST /run           → start an autonomous run, returns { run_id } immediately
  GET  /run/{run_id}  → run record + live agent logs + routes + report (frontend polls this)
  GET  /runs          → list past runs
"""
from __future__ import annotations

import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent / ".env")
except Exception:
    pass

from backend import db
from backend.agents import orchestrator

app = FastAPI(title="NexusAI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the Vercel URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)


class Delivery(BaseModel):
    id: str | None = None
    address: str
    lat: float | None = None
    lng: float | None = None


class Employee(BaseModel):
    id: str | None = None
    name: str
    role: str | None = None
    team: str | None = None
    email: str | None = None


class RunRequest(BaseModel):
    goal: str
    vertical: str = "logistics"          # "logistics" (default) or "hr"
    deliveries: list[Delivery] | None = None
    num_vehicles: int | None = 1
    employees: list[Employee] | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
async def start_run(req: RunRequest):
    if req.vertical == "hr":
        if not req.employees:
            raise HTTPException(status_code=422, detail="employees required for hr runs")
        employees = []
        for i, e in enumerate(req.employees):
            row = e.model_dump()
            row["id"] = row.get("id") or str(i + 1)
            employees.append(row)

        run_id = db.create_run(req.goal, 0, vertical="hr")  # num_vehicles unused for HR
        db.ctx_set(run_id, "vertical", "hr")
        db.ctx_set(run_id, "goal", req.goal)
        db.ctx_set(run_id, "employees", employees)
    else:
        deliveries = []
        for i, d in enumerate(req.deliveries or []):
            row = d.model_dump()
            row["id"] = row.get("id") or str(i + 1)
            deliveries.append(row)

        run_id = db.create_run(req.goal, req.num_vehicles or 1)
        db.ctx_set(run_id, "goal", req.goal)
        db.ctx_set(run_id, "deliveries", deliveries)
        db.ctx_set(run_id, "num_vehicles", req.num_vehicles or 1)

    # Run autonomously in the background so the client can poll progress live.
    asyncio.create_task(orchestrator.run_existing(run_id))
    return {"run_id": run_id, "status": "running"}


@app.get("/run/{run_id}")
def get_run(run_id: str):
    data = db.get_run(run_id)
    if not data["run"]:
        raise HTTPException(status_code=404, detail="run not found")
    return data


@app.get("/runs")
def list_runs():
    return db.list_runs()
