# NexusAI

**One goal. Five agents. Zero human intervention.**

![FAR AWAY 2026](https://img.shields.io/badge/FAR%20AWAY-2026%20Hackathon-blueviolet?style=for-the-badge)
![Theme](https://img.shields.io/badge/Theme-Agentic%20%26%20Autonomous%20Systems-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-In%20Development-orange?style=for-the-badge)

---

## What is NexusAI?

NexusAI is a multi-agent autonomous delivery system. You give it one plain-English goal — *"Deliver 40 packages across Pune by 6 PM"* — and five specialised AI agents coordinate end-to-end without any further human input.

---

## How It Works

| Agent | Role | What it does |
|---|---|---|
| **Orchestrator** | Coordinator | Receives the user goal, breaks it into tasks, delegates to specialist agents, and assembles the final result |
| **Planner** | Strategist | Analyses deliveries, groups them by zone, assigns vehicles, and builds the master delivery plan |
| **Route Optimizer** | Navigator | Runs route optimisation across all vehicle paths to minimise total distance and fuel cost |
| **Notification** | Communicator | Sends real-time status updates to customers and fleet managers via email |
| **Analytics** | Reporter | Calculates KPIs — distance saved, CO₂ avoided, cost saved, on-time rate — and generates the final report |

---

## Key Features

- **Single natural-language goal** triggers the entire pipeline
- **Fully autonomous** — agents call each other; no human checkpoints
- **Real route optimisation** using geospatial clustering
- **Live customer notifications** via Resend email API
- **Measurable impact** — CO₂ savings, cost reduction, time saved reported per run
- **Persistent run history** stored in Supabase with full agent logs

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI / Agents | Claude API (Anthropic) — claude-sonnet-4-6 |
| Backend | Python 3.11 · FastAPI · Uvicorn |
| Database | Supabase (PostgreSQL) |
| Notifications | Resend |
| Geospatial | Geopy |
| Frontend | Next.js 14 · TypeScript · Tailwind CSS |
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
| **Sameer Akhtar** | Lead Developer | Claude Pro |
| **Aditya Patil** | Frontend Developer | Claude Pro |
| **Aditya Adarsh** | Backend Agent Dev | Antigravity |
| **Chetan Prajapat** | Agent Dev & Presenter | Antigravity |

---

*Built at FAR AWAY 2026 — Agentic and Autonomous Systems track.*
