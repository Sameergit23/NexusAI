"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Rocket, Sparkles, Loader2 } from "lucide-react";
import { startRun, SAMPLE_DELIVERIES, SAMPLE_GOAL, type Delivery } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [goal, setGoal] = useState("");
  const [vehicles, setVehicles] = useState(2);
  const [text, setText] = useState("");
  const [sampleLoaded, setSampleLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function loadSample() {
    setGoal(SAMPLE_GOAL);
    setVehicles(2);
    setText(SAMPLE_DELIVERIES.map((d) => d.address).join("\n"));
    setSampleLoaded(true);
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

      <p className="mt-6 text-center text-xs text-gray-500 font-medium">
        5 agents · real OSRM routing · live impact report
      </p>
    </main>
  );
}
