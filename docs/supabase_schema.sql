-- NexusAI — Supabase Schema
-- Run this in your Supabase SQL editor before starting the backend.

-- ─────────────────────────────────────────────
-- 1. runs
-- One row per autonomous delivery run.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS runs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal         TEXT        NOT NULL,
    status       TEXT        NOT NULL DEFAULT 'pending',   -- pending | running | completed | failed
    num_vehicles INTEGER     NOT NULL DEFAULT 1,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- ─────────────────────────────────────────────
-- 2. agent_logs
-- Every agent action is appended here for traceability.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_logs (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id     UUID        NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    agent      TEXT        NOT NULL,   -- orchestrator | planner | route_optimizer | notification | analytics
    message    TEXT        NOT NULL,
    level      TEXT        NOT NULL DEFAULT 'info',        -- info | warning | error
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_logs_run_id ON agent_logs(run_id);

-- ─────────────────────────────────────────────
-- 3. deliveries
-- One row per package in a run.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS deliveries (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id     UUID        NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    address    TEXT        NOT NULL,
    lat        DOUBLE PRECISION,
    lng        DOUBLE PRECISION,
    zone_id    TEXT,
    status     TEXT        NOT NULL DEFAULT 'pending',     -- pending | in_transit | delivered | failed
    eta        TIMESTAMPTZ,
    route_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_deliveries_run_id ON deliveries(run_id);

-- ─────────────────────────────────────────────
-- 4. analytics
-- One row per completed run — KPI summary.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS analytics (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id            UUID            NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    naive_km          DOUBLE PRECISION NOT NULL,
    optimised_km      DOUBLE PRECISION NOT NULL,
    savings_km        DOUBLE PRECISION GENERATED ALWAYS AS (naive_km - optimised_km) STORED,
    savings_pct       DOUBLE PRECISION GENERATED ALWAYS AS (
                          CASE WHEN naive_km > 0
                               THEN ROUND(((naive_km - optimised_km) / naive_km * 100)::NUMERIC, 2)
                               ELSE 0
                          END
                      ) STORED,
    co2_avoided_kg    DOUBLE PRECISION,
    cost_saved_inr    DOUBLE PRECISION,
    time_saved_min    DOUBLE PRECISION,
    on_time_rate      DOUBLE PRECISION,                    -- 0.0 – 1.0
    trees_equivalent  DOUBLE PRECISION,
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_analytics_run_id ON analytics(run_id);
