# NexusAI

**Set the goal. Agents handle the rest.**

![FAR AWAY 2026](https://img.shields.io/badge/FAR%20AWAY-2026%20Hackathon-blueviolet?style=for-the-badge)
![Theme](https://img.shields.io/badge/Theme-Agentic%20%26%20Autonomous%20Systems-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-In%20Development-orange?style=for-the-badge)

---

## What is NexusAI?

**NexusAI is an Autonomous Agent Operating System.**

You type any operational goal in plain English, and **five specialised AI agents collaborate autonomously** to achieve it — planning, executing real actions, communicating, and reporting — with **no human in the loop** after the goal is set.

It is **not a chatbot** and **not a single-purpose logistics tool.** It is a universal multi-agent platform: the same five agents, pointed at a different domain, can run *any* operation. Logistics is simply our first demo vertical because it is visual, measurable, and universally relatable — you can literally watch routes draw on a map and measure the CO₂ and cost saved.

> **The vision:** state the outcome you want, and a team of AI agents executes the entire operation end-to-end — so humans set direction instead of doing the work.

---

## Why It's Genuinely Agentic (not a chatbot)

NexusAI strictly follows six principles:

1. **Goal-directed** — the user sets a goal, not a sequence of steps
2. **Multi-agent collaboration** — agents coordinate with each other, not with humans
3. **Real tool use** — real APIs and real actions, not just generated text
4. **Reasoning and planning** — Claude reasons about what to do next
5. **Autonomous failure recovery** — no human alert when something breaks; agents reschedule and retry
6. **Self-verification** — the system stops when the goal is verified complete, not on a fixed pipeline

---

## The Five Agents

| Agent | Role | What it does |
|---|---|---|
| **Orchestrator** | The brain | Receives the goal and runs an agentic loop with Claude tool-calling: reason → call agent → evaluate result → call next agent → continue until the goal is verified complete |
| **Planner** | Strategist | Breaks the goal into sub-tasks. For logistics: geocodes addresses and clusters deliveries into geographic zones, returning a structured zone map |
| **Route Optimizer** | Executor | Executes real actions. For logistics: calls the OSRM routing API for real road routes, distances, durations, and GeoJSON geometry per zone |
| **Communicator** | Messenger | Sends all messages. For logistics: uses Claude to generate personalised ETA emails and sends them via Resend, handling bounces autonomously |
| **Analytics** | Reporter | Auto-generates the outcome report — km saved, time saved, CO₂ avoided, cost saved, on-time rate, and trees-equivalent impact |

---

## One Platform, Many Verticals

The architecture is universal. The agents don't change; only the tools they call do.

**Round 1 demo:** Logistics & Delivery Operations
**Roadmap (15 categories):** Customer Support · Sales · HR · Healthcare · Finance · Education · Manufacturing · Real Estate · Travel · Legal · Government · and more

---

## Key Features

- **Single natural-language goal** triggers the entire pipeline
- **Fully autonomous** — agents call each other; no human checkpoints
- **Real route optimisation** using geocoding and the OSRM road-routing API
- **Live customer notifications** via the Resend email API
- **Measurable impact** — CO₂ savings, cost reduction, time saved reported per run
- **Persistent run history** stored in Supabase with full agent logs
- **Live dashboard** streaming each agent's reasoning and actions in real time

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI / Agents | Claude API (Anthropic) — claude-sonnet-4-6 with tool use |
| Backend | Python 3.11 · FastAPI · Uvicorn · Server-Sent Events |
| Database | Supabase (PostgreSQL) |
| Notifications | Resend |
| Geospatial | Geopy (geocoding) · OSRM (road routing) |
| Frontend | Next.js 14 · TypeScript · Tailwind CSS · Leaflet · Recharts |
| Deployment | Vercel (frontend) · Railway (backend) |

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Supabase project
- Anthropic API key
- Resend API key

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
cp ../.env.example ../.env
# Fill in your keys in .env
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp ../.env.example .env.local
# Set NEXT_PUBLIC_API_URL in .env.local
npm run dev
```

### Database

Run `docs/supabase_schema.sql` in your Supabase SQL editor to create all tables.

---

## Team

| Name | Role | Sponsor |
|---|---|---|
| **Sameer Akhtar** | Lead Developer · Integration & Deployment Lead | Claude Pro |
| **Aditya Patil** | Frontend Developer | Claude Pro |
| **Aditya Adarsh** | Backend Agent Developer | Antigravity |
| **Chetan Prajapat** | Backend Agent Developer & Presenter | Antigravity |

---

*Built at FAR AWAY 2026 — Agentic and Autonomous Systems track.*
