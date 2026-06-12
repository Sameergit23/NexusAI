"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Rocket, Sparkles, Loader2, Truck, Users } from "lucide-react";
import {
  startRun,
  SAMPLE_DELIVERIES,
  SAMPLE_GOAL,
  SAMPLE_EMPLOYEES,
  SAMPLE_HR_GOAL,
  type Delivery,
  type Employee,
  type Vertical,
} from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [vertical, setVertical] = useState<Vertical>("logistics");
  const [goal, setGoal] = useState("");
  const [vehicles, setVehicles] = useState(2);
  const [text, setText] = useState("");
  const [sampleLoaded, setSampleLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // HR form state
  const [hrGoal, setHrGoal] = useState("");
  const [hires, setHires] = useState(5);
  const [hrText, setHrText] = useState("");
  const [hrSampleLoaded, setHrSampleLoaded] = useState(false);

  function loadSample() {
    setGoal(SAMPLE_GOAL);
    setVehicles(2);
    setText(SAMPLE_DELIVERIES.map((d) => d.address).join("\n"));
    setSampleLoaded(true);
  }

  function loadHrSample() {
    setHrGoal(SAMPLE_HR_GOAL);
    setHires(SAMPLE_EMPLOYEES.length);
    setHrText(
      SAMPLE_EMPLOYEES.map((e) => `${e.name}, ${e.role}, ${e.team}, ${e.email}`).join("\n")
    );
    setHrSampleLoaded(true);
  }

  async function launch() {
    setError("");
    const deliveries: Delivery[] = sampleLoaded
      ? SAMPLE_DELIVERIES
      : text
          .split("\n")
          .map((l) => l.trim())
          .filter(Boolean)
          .map((address, i) => ({ id: String(i + 1), address }));

    if (!goal.trim() || deliveries.length === 0) {
      setError("Enter a goal and at least one delivery address.");
      return;
    }
    setBusy(true);
    try {
      const { run_id } = await startRun(goal, deliveries, vehicles);
      router.push(`/run/${run_id}`);
    } catch (e: any) {
      setError(e.message || "Failed to start the run.");
      setBusy(false);
    }
  }

  async function launchHr() {
    setError("");
    const employees: Employee[] = hrSampleLoaded
      ? SAMPLE_EMPLOYEES
      : hrText
          .split("\n")
          .map((l) => l.trim())
          .filter(Boolean)
          .map((line, i) => {
            const [name, role, team, email] = line.split(",").map((s) => s.trim());
            return { id: String(i + 1), name: name || `Hire ${i + 1}`, role, team, email };
          });

    if (!hrGoal.trim() || employees.length === 0) {
      setError("Enter a goal and at least one employee.");
      return;
    }
    setBusy(true);
    try {
      const { run_id } = await startRun(hrGoal, employees, "hr");
      router.push(`/run/${run_id}`);
    } catch (e: any) {
      setError(e.message || "Failed to start the run.");
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-6 py-16">
      <div className="mb-10 text-center">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1 text-xs text-indigo-600 font-semibold shadow-sm">
          <Sparkles size={14} /> Autonomous Agent Operating System
        </div>
        <h1 className="text-5xl font-extrabold tracking-tight text-gray-900">
          NexusAI
        </h1>
        <p className="mt-3 text-lg text-gray-600">Set the goal. Agents handle the rest.</p>
      </div>

      {/* Vertical switcher */}
      <div className="mb-5 grid grid-cols-2 gap-3">
        <button
          onClick={() => { setVertical("logistics"); setError(""); }}
          className={`flex items-center gap-3 rounded-xl border bg-white p-4 text-left shadow-soft transition ${
            vertical === "logistics"
              ? "border-indigo-500 ring-1 ring-indigo-500"
              : "border-gray-200 hover:border-gray-300"
          }`}
        >
          <Truck size={20} className={vertical === "logistics" ? "text-indigo-600" : "text-gray-400"} />
          <span>
            <span className="block text-sm font-bold text-gray-900">Logistics</span>
            <span className="text-xs font-semibold text-emerald-600">LIVE</span>
          </span>
        </button>
        <button
          onClick={() => { setVertical("hr"); setError(""); }}
          className={`flex items-center gap-3 rounded-xl border bg-white p-4 text-left shadow-soft transition ${
            vertical === "hr"
              ? "border-indigo-500 ring-1 ring-indigo-500"
              : "border-gray-200 hover:border-gray-300"
          }`}
        >
          <Users size={20} className={vertical === "hr" ? "text-indigo-600" : "text-gray-400"} />
          <span>
            <span className="block text-sm font-bold text-gray-900">HR Onboarding</span>
            <span className="text-xs font-semibold text-indigo-600">NEW</span>
          </span>
        </button>
      </div>

      {vertical === "logistics" ? (
      <div className="space-y-5 rounded-xl border border-gray-200 bg-white p-6 shadow-soft">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Operational Goal</label>
          <textarea
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            rows={2}
            placeholder="e.g. Deliver 10 packages across Pune today, minimise distance, notify customers"
            className="w-full resize-none rounded-lg border border-gray-300 bg-gray-50 p-3 text-sm text-gray-900 outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 focus:bg-white transition"
          />
        </div>

        <div className="flex gap-4">
          <div className="w-32">
            <label className="mb-1 block text-sm font-medium text-gray-700">Vehicles</label>
            <input
              type="number"
              min={1}
              value={vehicles}
              onChange={(e) => setVehicles(Math.max(1, Number(e.target.value)))}
              className="w-full rounded-lg border border-gray-300 bg-gray-50 p-3 text-sm text-gray-900 outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 focus:bg-white transition"
            />
          </div>
          <div className="flex-1 flex flex-col justify-end">
            <label className="mb-1 block text-sm font-medium text-gray-700">Deliveries (one address per line)</label>
            <div>
              <button
                onClick={loadSample}
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 hover:underline"
              >
                ↳ load Pune sample
              </button>
            </div>
          </div>
        </div>

        <textarea
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            setSampleLoaded(false);
          }}
          rows={6}
          placeholder={"FC Road, Pune\nKoregaon Park, Pune\n..."}
          className="w-full resize-none rounded-lg border border-gray-300 bg-gray-50 p-3 text-sm text-gray-900 outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 focus:bg-white transition"
        />

        {error && <p className="text-sm font-medium text-red-600">{error}</p>}

        <button
          onClick={launch}
          disabled={busy}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-3 font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:opacity-60"
        >
          {busy ? <Loader2 className="animate-spin" size={18} /> : <Rocket size={18} />}
          {busy ? "Launching agents…" : "Launch Agents"}
        </button>
      </div>
      ) : (
      <div className="space-y-5 rounded-xl border border-gray-200 bg-white p-6 shadow-soft">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Operational Goal</label>
          <textarea
            value={hrGoal}
            onChange={(e) => setHrGoal(e.target.value)}
            rows={2}
            placeholder="Onboard 5 engineers joining Monday..."
            className="w-full resize-none rounded-lg border border-gray-300 bg-gray-50 p-3 text-sm text-gray-900 outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 focus:bg-white transition"
          />
        </div>

        <div className="flex gap-4">
          <div className="w-32">
            <label className="mb-1 block text-sm font-medium text-gray-700">New hires</label>
            <input
              type="number"
              min={1}
              value={hires}
              onChange={(e) => setHires(Math.max(1, Number(e.target.value)))}
              className="w-full rounded-lg border border-gray-300 bg-gray-50 p-3 text-sm text-gray-900 outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 focus:bg-white transition"
            />
          </div>
          <div className="flex-1 flex flex-col justify-end">
            <label className="mb-1 block text-sm font-medium text-gray-700">Employees (name, role, team, email per line)</label>
            <div>
              <button
                onClick={loadHrSample}
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 hover:underline"
              >
                ↳ load HR sample
              </button>
            </div>
          </div>
        </div>

        <textarea
          value={hrText}
          onChange={(e) => {
            setHrText(e.target.value);
            setHrSampleLoaded(false);
          }}
          rows={6}
          placeholder={"Priya Sharma, Backend Engineer, Platform, priya@nexusai.demo\nArjun Mehta, Frontend Engineer, Web, arjun@nexusai.demo\n..."}
          className="w-full resize-none rounded-lg border border-gray-300 bg-gray-50 p-3 text-sm text-gray-900 outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 focus:bg-white transition"
        />

        {error && <p className="text-sm font-medium text-red-600">{error}</p>}

        <button
          onClick={launchHr}
          disabled={busy}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-3 font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:opacity-60"
        >
          {busy ? <Loader2 className="animate-spin" size={18} /> : <Rocket size={18} />}
          {busy ? "Launching agents…" : "Launch Agents"}
        </button>
      </div>
      )}

      <p className="mt-6 text-center text-xs text-gray-500 font-medium">
        {vertical === "logistics"
          ? "5 agents · real OSRM routing · live impact report"
          : "5 agents · same OS, new vertical · live readiness report"}
      </p>
    </main>
  );
}
