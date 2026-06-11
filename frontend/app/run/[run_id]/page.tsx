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
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import mockData from "@/mock/run.json";

const AGENT_META: Record<AgentName, { label: string; icon: any }> = {
  orchestrator: { label: "Orchestrator", icon: Brain },
  planner: { label: "Planner", icon: MapIcon },
  route_optimizer: { label: "Router", icon: Route },
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
      } catch (err) {
        const apiEnv = process.env.NEXT_PUBLIC_API_URL;
        if (!apiEnv || apiEnv === "http://localhost:8000") {
          setData(mockData as any);
          clearInterval(timer.current);
        }
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

  const chartData = useMemo(() => {
    if (!report) return [];
    return [
      {
        name: "Distance (km)",
        Naive: report.naive_km,
        Optimised: report.optimised_km,
      },
    ];
  }, [report]);

  return (
    <main className="mx-auto max-w-6xl px-6 py-8">
      <header className="mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-extrabold text-gray-900">NexusAI</h1>
          <StatusBadge status={status} />
        </div>
        <p className="mt-2 text-sm font-medium text-gray-600">{data?.run?.goal}</p>
      </header>

      {/* Agent cards */}
      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-5">
        {AGENTS.map((a, i) => {
          const { label, icon: Icon } = AGENT_META[a];
          const st = agentState(i);
          return (
            <div
              key={a}
              className={`rounded-lg bg-white p-4 shadow-soft border border-gray-200 border-l-4 transition ${
                st === "running"
                  ? "border-l-indigo-500 bg-indigo-50/10"
                  : st === "done"
                  ? "border-l-emerald-500 bg-emerald-50/10"
                  : "border-l-gray-300"
              }`}
            >
              <div className="flex items-center justify-between">
                <Icon size={18} className="text-gray-500" />
                {st === "done" ? (
                  <CheckCircle2 size={16} className="text-emerald-500" />
                ) : st === "running" ? (
                  <Loader2 size={16} className="animate-spin text-indigo-500" />
                ) : (
                  <Circle size={16} className="text-gray-300" />
                )}
              </div>
              <p className="mt-2 text-sm font-bold text-gray-800">{label}</p>
              <p className="text-xs font-semibold capitalize text-gray-500">{st}</p>
            </div>
          );
        })}
      </div>

      {/* Recharts Distance Comparison (Naive vs Optimised) */}
      {report && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-5 shadow-soft">
          <h2 className="mb-4 text-sm font-semibold text-gray-700">Distance Optimization (Naive vs. Optimised)</h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <XAxis dataKey="name" stroke="#4b5563" fontSize={12} tickLine={false} />
                <YAxis stroke="#4b5563" fontSize={12} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e5e7eb", borderRadius: "8px" }}
                  itemStyle={{ color: "#1f2937" }}
                  labelStyle={{ color: "#4b5563" }}
                />
                <Bar dataKey="Naive" fill="#6366f1" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Optimised" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Map */}
        <div className="lg:col-span-2">
          <div className="h-[420px] overflow-hidden rounded-lg border border-gray-200 bg-white p-1 shadow-soft">
            <MapView routes={data?.routes ?? null} />
          </div>
        </div>

        {/* Live log feed */}
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 shadow-soft">
          <h2 className="mb-3 text-sm font-semibold text-gray-700">Agent reasoning log</h2>
          <div className="flex max-h-[372px] flex-col gap-2 overflow-y-auto font-mono text-xs text-gray-600">
            {logs.map((l, i) => (
              <div key={i} className="border-l-2 border-gray-300 pl-2 py-0.5">
                <span
                  className={`font-semibold ${
                    l.level === "error"
                      ? "text-red-600"
                      : l.level === "warning"
                      ? "text-amber-600"
                      : "text-indigo-600"
                  }`}
                >
                  {l.agent}
                </span>
                <p className="text-gray-700 mt-0.5">{l.message}</p>
              </div>
            ))}
            {logs.length === 0 && <p className="text-gray-400 italic">Waiting for agents…</p>}
          </div>
        </div>
      </div>

      {/* Impact report */}
      {report && (
        <section className="mt-6">
          <h2 className="mb-3 text-sm font-semibold text-gray-700">Impact report</h2>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Metric icon={TrendingDown} label="Distance saved" value={`${report.savings_km} km`} sub={`${report.savings_pct}% shorter`} />
            <Metric icon={Leaf} label="CO₂ avoided" value={`${report.co2_avoided_kg} kg`} sub={`${report.trees_equivalent} trees/yr`} />
            <Metric icon={IndianRupee} label="Cost saved" value={`₹${report.cost_saved_inr}`} />
            <Metric icon={Clock} label="Time saved" value={`${report.time_saved_min} min`} sub={`${Math.round(report.on_time_rate * 100)}% on-time`} />
          </div>
          <div className="mt-3 rounded-lg border border-gray-200 bg-white p-4 text-sm text-gray-600 shadow-soft">
            Naive routing: <b className="text-gray-900 font-semibold">{report.naive_km} km</b> →
            optimised: <b className="text-emerald-600 font-bold">{report.optimised_km} km</b>
          </div>
        </section>
      )}
    </main>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    running: "border-indigo-200 bg-indigo-50 text-indigo-700",
    completed: "border-emerald-200 bg-emerald-50 text-emerald-700",
    failed: "border-red-200 bg-red-50 text-red-700",
  };
  return (
    <span className={`rounded-full border px-3 py-1 text-xs font-semibold capitalize shadow-sm ${map[status] ?? "border-gray-200 bg-gray-50 text-gray-600"}`}>
      {status}
    </span>
  );
}

function Metric({ icon: Icon, label, value, sub }: { icon: any; label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-soft">
      <Icon size={18} className="text-indigo-500" />
      <p className="mt-2 text-xl font-bold text-gray-900">{value}</p>
      <p className="text-xs font-semibold text-gray-500">{label}</p>
      {sub && <p className="text-xs font-semibold text-emerald-600">{sub}</p>}
    </div>
  );
}
