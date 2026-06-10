# NexusAI — System Architecture

## Overview

NexusAI is an **Autonomous Agent Operating System** — a universal multi-agent platform where a single user goal is achieved end-to-end by five specialised Claude agents with no human in the loop. The architecture is domain-agnostic: the agents stay the same across verticals (Logistics, Customer Support, Sales, HR, Healthcare, Finance, and more); only the tools they call change.

This document describes the **Round 1 logistics vertical**, our first and most visual demo. A single user goal flows through the five agents. Each agent calls one or more tools, persists its output to Supabase, and passes a structured result to the next agent. No human intervention is required after the initial goal is submitted.

---

## End-to-End Data Flow

```
User
 │
 │  "Deliver 40 packages across Pune by 6 PM, 3 vehicles"
 ▼
┌─────────────────────────────────────────────────────────────┐
│  Orchestrator Agent                                         │
│  • Parses the goal                                          │
│  • Creates a run record in Supabase (status = running)      │
│  • Delegates in order: Planner → Route Optimizer →          │
│    Notification → Analytics                                 │
│  • Assembles and returns the final result                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ plan_request (goal, deliveries, num_vehicles)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Planner Agent                          Tool: plan_tasks    │
│  • Geocodes addresses                                       │
│  • Clusters deliveries into N zones (one per vehicle)       │
│  • Returns zone assignments + vehicle mapping               │
└──────────────────────────┬──────────────────────────────────┘
                           │ zones[] (zone_id, vehicle_id, deliveries[])
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Route Optimizer Agent              Tool: optimise_routes   │
│  • Runs nearest-neighbour / TSP heuristic per zone          │
│  • Calculates optimised_km and naive_km                     │
│  • Writes route_data to deliveries table                    │
│  • Returns per-vehicle ordered waypoint lists + distances   │
└──────────────────────────┬──────────────────────────────────┘
                           │ optimised_routes[], naive_km, optimised_km
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Notification Agent             Tool: send_notifications    │
│  • Builds personalised email per customer (ETA, address)    │
│  • Sends via Resend API                                     │
│  • Logs message IDs to agent_logs                           │
└──────────────────────────┬──────────────────────────────────┘
                           │ notification_results[]
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Analytics Agent                    Tool: generate_report   │
│  • Computes KPIs (savings_km, savings_pct, CO₂, cost, etc.) │
│  • Writes row to analytics table                            │
│  • Updates run status = completed                           │
│  • Returns final summary JSON                               │
└──────────────────────────┬──────────────────────────────────┘
                           │ final_report
                           ▼
                         User / Frontend
```

---

## Agent Contracts

### Orchestrator
| | |
|---|---|
| **Input** | `{ goal: str, deliveries: list, num_vehicles: int }` |
| **Output** | `{ run_id: str, plan: obj, routes: obj, notifications: obj, report: obj }` |
| **Supabase writes** | `runs` (create + status update) |

### Planner
| | |
|---|---|
| **Input** | `{ goal: str, deliveries: [{id, address, lat?, lng?}], num_vehicles: int }` |
| **Output** | `{ zones: [{zone_id, vehicle_id, deliveries[]}] }` |
| **Supabase writes** | `deliveries` (insert rows), `agent_logs` |

### Route Optimizer
| | |
|---|---|
| **Input** | `{ run_id: str, zones: [{zone_id, vehicle_id, deliveries[]}] }` |
| **Output** | `{ routes: [{vehicle_id, ordered_stops[], total_km}], naive_km, optimised_km }` |
| **Supabase writes** | `deliveries` (update route_data, eta), `agent_logs` |

### Notification
| | |
|---|---|
| **Input** | `{ run_id: str, notifications: [{to, subject, body, delivery_id?}] }` |
| **Output** | `{ sent: [{delivery_id, message_id}], failed: [] }` |
| **Supabase writes** | `agent_logs` |

### Analytics
| | |
|---|---|
| **Input** | `{ run_id: str, naive_km, optimised_km, deliveries_total, deliveries_on_time }` |
| **Output** | `{ savings_km, savings_pct, co2_avoided_kg, cost_saved_inr, time_saved_min, on_time_rate, trees_equivalent }` |
| **Supabase writes** | `analytics` (insert), `runs` (status = completed) |

---

## Folder Structure

```
NexusAI/
├── .env.example                  # Key template — copy to .env
├── .gitignore
├── README.md
│
├── backend/
│   ├── main.py                   # FastAPI app + /run endpoint  [Phase 2]
│   ├── requirements.txt
│   │
│   ├── agents/
│   │   ├── orchestrator.py       # [Phase 2]
│   │   ├── planner.py            # [Phase 2]
│   │   ├── route_optimizer.py    # [Phase 2]
│   │   ├── notification.py       # [Phase 2]
│   │   └── analytics.py          # [Phase 2]
│   │
│   └── tools/
│       ├── definitions.py        # ALL_TOOLS list for Claude API
│       └── handlers.py           # Tool execution logic  [Phase 2]
│
├── frontend/                     # Next.js app  [Phase 3]
│
└── docs/
    ├── ARCHITECTURE.md           # This file
    └── supabase_schema.sql       # Run in Supabase SQL editor
```

---

## Key Design Decisions

**Why Claude tool use instead of direct function calls?**
Each agent runs in its own Claude API call with a curated subset of `ALL_TOOLS`. The agent decides *when* and *how* to call a tool based on the goal, enabling natural reasoning chains without hard-coded if/else logic.

**Why Supabase?**
Real-time subscriptions let the frontend stream live agent logs and delivery status updates without polling.

**Why separate agents vs one big prompt?**
Separation enforces clean interfaces (each agent has typed inputs/outputs), makes individual agents testable in isolation, and lets the Orchestrator retry a failing agent without re-running the whole pipeline.
