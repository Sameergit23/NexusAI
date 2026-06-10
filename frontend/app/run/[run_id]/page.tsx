"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import {
  Brain, Map as MapIcon, Route, Mail, BarChart3, CheckCircle2, Loader2, Circle,
  Leaf, IndianRupee, Clock, TrendingDown,
} from "lucide-react";
import { getRun, AGENTS, type RunResponse, type AgentName } from "@/lib/api";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

const AGENT_META: Record<AgentName, { label: string; icon: any }> = {
  orchestrator: { label: "Orchestrator", icon: Brain },
  planner: { label: "Planner", icon: MapIcon },
  route_optimizer: { label: "Route Optimizer", icon: Route },
  notification: { label: "Communicator", icon: Mail },
  analytics: { label: "Analytics", icon: BarChart3 },
};

export default function RunPage() {
  const { run_id } = useParams<{ run_id: string }>();
  const [data, setData] = useState<RunResponse | null>(null);
  const timer = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    async function poll() {
      try {
        const d = await getRun(run_id);
        setData(d);
        if (d.run?.status === "completed" || d.run?.status === "failed") {
          clearInterval(timer.current);
        }
      } catch {
        /* keep polling */
      }
    }
    poll();
    timer.current = setInterval(poll, 2000);
    return () => clearInterval(timer.current);
  }, [run_id]);

  const status = data?.run?.status ?? "running";
  const logs = data?.logs ?? [];
  const report = data?.report ?? data?.analytics ?? null;

  // Derive each agent's state from the log stream (sequential animation).
  const lastAgentIdx = useMemo(() => {
    let idx = -1;
    for (const l of logs) {
      const i = AGENTS.indexOf(l.agent as AgentName);
      if (i > idx) idx = i;
    }
    return idx;
  }, [logs]);

  function agentState(i: number): "done" | "running" | "pending" {
    if (status === "completed") return "done";
    if (i < lastAgentIdx) return "done";
    if (i === lastAgentIdx) return "running";
    return "pending";
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-8">
      <header className="mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-indigo-300">NexusAI</h1>
          <StatusBadge status={status} />
        </div>
        <p className="mt-1 text-sm text-gray-400">{data?.run?.goal}</p>
      </header>

      {/* Agent cards */}
      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-5">
        {AGENTS.map((a, i) => {
          const { label, icon: Icon } = AGENT_META[a];
          const st = agentState(i);
          return (
            <div
              key={a}
              className={`rounded-xl border p-3 ${
                st === "running"
                  ? "border-nexus-accent bg-indigo-500/10"
                  : st === "done"
                  ? "border-nexus-good/40 bg-emerald-500/5"
                  : "border-nexus-border bg-nexus-panel"
              }`}
            >
              <div className="flex items-center justify-between">
                <Icon size={18} className="text-gray-300" />
                {st === "done" ? (
                  <CheckCircle2 size={16} className="text-nexus-good" />
                ) : st === "running" ? (
                  <Loader2 size={16} className="animate-spin text-nexus-accent" />
                ) : (
                  <Circle size={16} className="text-gray-600" />
                )}
              </div>
              <p className="mt-2 text-sm font-medium">{label}</p>
              <p className="text-xs capitalize text-gray-500">{st}</p>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Map */}
        <div className="lg:col-span-2">
          <div className="h-[420px] overflow-hidden rounded-xl border border-nexus-border">
            <MapView routes={data?.routes ?? null} />
          </div>
        </div>

        {/* Live log feed */}
        <div className="rounded-xl border border-nexus-border bg-nexus-panel p-4">
          <h2 className="mb-3 text-sm font-semibold text-gray-300">Agent reasoning log</h2>
          <div className="flex max-h-[372px] flex-col gap-2 overflow-y-auto text-xs">
            {logs.map((l, i) => (
              <div key={i} className="border-l-2 border-nexus-border pl-2">
                <span
                  className={`font-mono ${
                    l.level === "error"
                      ? "text-red-400"
                      : l.level === "warning"
                      ? "text-amber-400"
                      : "text-nexus-accent2"
                  }`}
                >
                  {l.agent}
                </span>
                <p className="text-gray-300">{l.message}</p>
              </div>
            ))}
            {logs.length === 0 && <p className="text-gray-600">Waiting for agents…</p>}
          </div>
        </div>
      </div>

      {/* Impact report */}
      {report && (
        <section className="mt-6">
          <h2 className="mb-3 text-sm font-semibold text-gray-300">Impact report</h2>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Metric icon={TrendingDown} label="Distance saved" value={`${report.savings_km} km`} sub={`${report.savings_pct}% shorter`} />
            <Metric icon={Leaf} label="CO₂ avoided" value={`${report.co2_avoided_kg} kg`} sub={`${report.trees_equivalent} trees/yr`} />
            <Metric icon={IndianRupee} label="Cost saved" value={`₹${report.cost_saved_inr}`} />
            <Metric icon={Clock} label="Time saved" value={`${report.time_saved_min} min`} sub={`${Math.round(report.on_time_rate * 100)}% on-time`} />
          </div>
          <div className="mt-3 rounded-xl border border-nexus-border bg-nexus-panel p-4 text-sm text-gray-400">
            Naive routing: <b className="text-gray-200">{report.naive_km} km</b> →
            optimised: <b className="text-nexus-good">{report.optimised_km} km</b>
          </div>
        </section>
      )}
    </main>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    running: "border-nexus-accent text-nexus-accent",
    completed: "border-nexus-good text-nexus-good",
    failed: "border-red-500 text-red-400",
  };
  return (
    <span className={`rounded-full border px-3 py-1 text-xs capitalize ${map[status] ?? "border-gray-600 text-gray-400"}`}>
      {status}
    </span>
  );
}

function Metric({ icon: Icon, label, value, sub }: { icon: any; label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-nexus-border bg-nexus-panel p-4">
      <Icon size={18} className="text-nexus-accent2" />
      <p className="mt-2 text-xl font-bold text-gray-100">{value}</p>
      <p className="text-xs text-gray-400">{label}</p>
      {sub && <p className="text-xs text-nexus-good">{sub}</p>}
    </div>
  );
}
