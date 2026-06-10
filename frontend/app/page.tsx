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
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-nexus-border bg-nexus-panel px-3 py-1 text-xs text-nexus-accent2">
          <Sparkles size={14} /> Autonomous Agent Operating System
        </div>
        <h1 className="bg-gradient-to-r from-indigo-400 to-cyan-300 bg-clip-text text-5xl font-bold text-transparent">
          NexusAI
        </h1>
        <p className="mt-3 text-lg text-gray-400">Set the goal. Agents handle the rest.</p>
      </div>

      <div className="space-y-4 rounded-2xl border border-nexus-border bg-nexus-panel p-6">
        <div>
          <label className="mb-1 block text-sm text-gray-400">Operational goal</label>
          <textarea
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            rows={2}
            placeholder="e.g. Deliver 10 packages across Pune today, minimise distance, notify customers"
            className="w-full resize-none rounded-lg border border-nexus-border bg-nexus-bg p-3 text-sm outline-none focus:border-nexus-accent"
          />
        </div>

        <div className="flex gap-4">
          <div className="w-32">
            <label className="mb-1 block text-sm text-gray-400">Vehicles</label>
            <input
              type="number"
              min={1}
              value={vehicles}
              onChange={(e) => setVehicles(Math.max(1, Number(e.target.value)))}
              className="w-full rounded-lg border border-nexus-border bg-nexus-bg p-3 text-sm outline-none focus:border-nexus-accent"
            />
          </div>
          <div className="flex-1">
            <label className="mb-1 block text-sm text-gray-400">Deliveries (one address per line)</label>
            <button
              onClick={loadSample}
              className="text-xs text-nexus-accent2 hover:underline"
            >
              ↳ load Pune sample
            </button>
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
          className="w-full resize-none rounded-lg border border-nexus-border bg-nexus-bg p-3 text-sm outline-none focus:border-nexus-accent"
        />

        {error && <p className="text-sm text-red-400">{error}</p>}

        <button
          onClick={launch}
          disabled={busy}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-nexus-accent px-4 py-3 font-medium text-white transition hover:bg-indigo-500 disabled:opacity-60"
        >
          {busy ? <Loader2 className="animate-spin" size={18} /> : <Rocket size={18} />}
          {busy ? "Launching agents…" : "Launch Agents"}
        </button>
      </div>

      <p className="mt-6 text-center text-xs text-gray-600">
        5 agents · real OSRM routing · live impact report
      </p>
    </main>
  );
}
