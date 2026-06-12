"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import {
  Brain, Map as MapIcon, Route, Mail, BarChart3, CheckCircle2, Loader2, Circle,
  Leaf, IndianRupee, Clock, TrendingDown, Users, ClipboardCheck,
  ChevronDown, ChevronUp, ArrowRight, AlertTriangle,
} from "lucide-react";
import {
  getRun, AGENTS,
  type RunResponse, type AgentName, type Report, type HrReport,
} from "@/lib/api";

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

// Same 5 cards, HR labels (see docs/hr-onboarding/OVERVIEW.md)
const AGENT_META_HR: Record<AgentName, { label: string; icon: any }> = {
  orchestrator: { label: "Orchestrator", icon: Brain },
  planner: { label: "HR Planner", icon: Users },
  route_optimizer: { label: "Onboarding Scheduler", icon: Clock },
  notification: { label: "HR Communicator", icon: Mail },
  analytics: { label: "HR Reporter", icon: BarChart3 },
};

const HR_AGENT_ALIAS: Record<string, AgentName> = {
  hr_planner: "planner",
  onboarding_scheduler: "route_optimizer",
  hr_communicator: "notification",
  hr_reporter: "analytics",
};

export default function RunPage() {
  const { run_id } = useParams<{ run_id: string }>();
  const [data, setData] = useState<RunResponse | null>(null);
  const [showActivity, setShowActivity] = useState(false);
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
  const vertical = data?.run?.vertical ?? "logistics";
  const hr = vertical === "hr";
  const meta = hr ? AGENT_META_HR : AGENT_META;
  const report = data?.report ?? data?.analytics ?? null;
  const lgReport = !hr ? (report as Report | null) : null;
  const hrReport = hr ? (report as HrReport | null) : null;
  const lastLog = logs.length > 0 ? logs[logs.length - 1] : null;

  // Derive each agent's state from the log stream (sequential animation).
  // HR agents log under their own names — map them onto the same 5 card slots.
  const lastAgentIdx = useMemo(() => {
    let idx = -1;
    for (const l of logs) {
      const name = (HR_AGENT_ALIAS[l.agent] ?? l.agent) as AgentName;
      const i = AGENTS.indexOf(name);
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
    if (!lgReport) return [];
    return [
      {
        name: "Distance (km)",
        Naive: lgReport.naive_km,
        Optimised: lgReport.optimised_km,
      },
    ];
  }, [lgReport]);

  return (
    <main className="mx-auto max-w-6xl px-6 py-8">
      <header className="mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-extrabold text-gray-900">NexusAI</h1>
          <StatusBadge status={status} />
        </div>
        <p className="mt-2 text-sm font-medium text-gray-600">{data?.run?.goal}</p>
      </header>

      {/* While running: a calm progress hero, no machinery */}
      {!report && status === "running" && (
        <div className="mb-6 flex flex-col items-center justify-center rounded-lg border border-gray-200 bg-white px-6 py-12 shadow-soft">
          <Loader2 size={28} className="animate-spin text-indigo-500" />
          <p className="mt-4 text-base font-semibold text-gray-800">
            {hr ? "Onboarding in progress…" : "Optimising your operation…"}
          </p>
          <p className="mt-1 text-sm text-gray-500">
            {lastLog ? lastLog.message : "Starting agents…"}
          </p>
        </div>
      )}

      {/* Failed: say so plainly */}
      {status === "failed" && (
        <div className="mb-6 flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 px-5 py-4">
          <AlertTriangle size={18} className="mt-0.5 shrink-0 text-red-600" />
          <div>
            <p className="text-sm font-semibold text-red-700">This run could not be completed.</p>
            <p className="mt-0.5 text-sm text-red-600">
              {[...logs].reverse().find((l) => l.level === "error")?.message ?? "Check the agent activity below for details."}
            </p>
          </div>
        </div>
      )}

      {/* THE RESULT — first thing a finished run shows */}
      {hrReport && (
        <section className="mb-6">
          <h2 className="mb-3 text-sm font-semibold text-gray-700">Readiness report</h2>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Metric icon={Users} label="Hires onboarded" value={`${hrReport.total_hires}`} />
            <Metric icon={ClipboardCheck} label="Tasks completed" value={`${hrReport.tasks_completed}/${hrReport.tasks_total}`} sub={`${hrReport.readiness_pct}% ready`} />
            <Metric icon={IndianRupee} label="Cost saved" value={`₹${hrReport.cost_saved_inr}`} />
            <Metric icon={Clock} label="Hours saved" value={`${hrReport.hours_saved} h`} sub={`${hrReport.emails_sent} welcome emails sent`} />
          </div>
        </section>
      )}

      {lgReport && (
        <section className="mb-6">
          <h2 className="mb-3 text-sm font-semibold text-gray-700">Impact report</h2>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Metric icon={TrendingDown} label="Distance saved" value={`${lgReport.savings_km} km`} sub={`${lgReport.savings_pct}% shorter`} />
            <Metric icon={Leaf} label="CO₂ avoided" value={`${lgReport.co2_avoided_kg} kg`} sub={`${lgReport.trees_equivalent} trees/yr`} />
            <Metric icon={IndianRupee} label="Cost saved" value={`₹${lgReport.cost_saved_inr}`} />
            <Metric icon={Clock} label="Time saved" value={`${lgReport.time_saved_min} min`} sub={`${Math.round(lgReport.on_time_rate * 100)}% on-time`} />
          </div>
          <div className="mt-3 rounded-lg border border-gray-200 bg-white p-4 text-sm text-gray-600 shadow-soft">
            Naive routing: <b className="text-gray-900 font-semibold">{lgReport.naive_km} km</b> →
            optimised: <b className="text-emerald-600 font-bold">{lgReport.optimised_km} km</b>
          </div>
        </section>
      )}

      {/* Map is a result too — logistics only */}
      {!hr && (
        <div className="mb-6">
          <div className="h-[420px] overflow-hidden rounded-lg border border-gray-200 bg-white p-1 shadow-soft">
            <MapView routes={data?.routes ?? null} />
          </div>
        </div>
      )}

      {/* Slim "how it was done" strip — the 5 agents, one line */}
      <div className="mb-6 flex flex-wrap items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-3 shadow-soft">
        <span className="mr-1 text-xs font-semibold text-gray-500">
          {status === "completed" ? "How it was done:" : "Agents:"}
        </span>
        {AGENTS.map((a, i) => {
          const { label } = meta[a];
          const st = agentState(i);
          return (
            <span key={a} className="flex items-center gap-2">
              <span
                className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${
                  st === "done"
                    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                    : st === "running"
                    ? "border-indigo-200 bg-indigo-50 text-indigo-700"
                    : "border-gray-200 bg-gray-50 text-gray-400"
                }`}
              >
                {st === "done" ? (
                  <CheckCircle2 size={13} />
                ) : st === "running" ? (
                  <Loader2 size={13} className="animate-spin" />
                ) : (
                  <Circle size={13} />
                )}
                {label}
              </span>
              {i < AGENTS.length - 1 && <ArrowRight size={12} className="text-gray-300" />}
            </span>
          );
        })}
      </div>

      {/* Distance chart — supporting detail, logistics only */}
      {lgReport && (
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

      {/* Raw agent activity — collapsed by default, for the curious (and the judges) */}
      <div className="rounded-lg border border-gray-200 bg-gray-50 shadow-soft">
        <button
          onClick={() => setShowActivity((v) => !v)}
          className="flex w-full items-center justify-between px-4 py-3 text-sm font-semibold text-gray-600 hover:text-gray-900"
        >
          <span>View agent activity ({logs.length} log entries)</span>
          {showActivity ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
        {showActivity && (
          <div className="border-t border-gray-200 p-4">
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
        )}
      </div>
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
