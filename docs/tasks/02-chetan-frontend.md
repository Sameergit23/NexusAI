# Tasks — Chetan Prajapat (Frontend · Vercel · Live Presenter)

**Your folder:** all of `frontend/` (Next.js 14 + TypeScript + Tailwind)
**Contracts:** the JSON shapes you render come from `docs/ARCHITECTURE.md`.
**Key tip:** build against **mock JSON first** — do not wait for the backend.

---

## PART A — Project setup

### A1. Scaffold the app
```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --app --eslint
```

### A2. Install libraries
```bash
npm install @supabase/supabase-js lucide-react leaflet react-leaflet recharts
npm install -D @types/leaflet
```
- ✅ **Done when:** `npm run dev` shows the default page at `localhost:3000`.

### A3. Environment + dark theme base
- Create `.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Set a dark background + base font in `app/globals.css` / `layout.tsx`.
- ✅ **Done when:** the page loads dark-themed and `process.env.NEXT_PUBLIC_API_URL` is readable.

---

## PART B — Home page (`app/page.tsx`)

### B1. Layout
- NexusAI title + tagline "Set the goal. Agents handle the rest."

### B2. Inputs (controlled React state)
- Goal `<textarea>` · Number-of-vehicles `<input type=number>` · Deliveries `<textarea>` (one address per line).

### B3. "Launch Agents" button → call the API
```ts
const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/run`, {
  method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    goal,
    num_vehicles: Number(vehicles),
    deliveries: addresses.split("\n").filter(Boolean)
                          .map((a, i) => ({ id: String(i+1), address: a })),
  }),
});
const { run_id } = await res.json();
router.push(`/run/${run_id}`);
```
- ✅ **Done when:** submitting redirects to `/run/<id>`.

---

## PART C — Live dashboard (`app/run/[run_id]/page.tsx`)

### C1. Polling hook
```ts
useEffect(() => {
  const t = setInterval(async () => {
    const data = await fetch(`${API}/run/${run_id}`).then(r => r.json());
    setRun(data.run); setLogs(data.logs);
    if (data.run.status === "completed") clearInterval(t);
  }, 2000);
  return () => clearInterval(t);
}, [run_id]);
```

### C2. Goal header — show `run.goal` + a status badge (running/completed).

### C3. 5 agent status cards
- One card each: Orchestrator, Planner, Route Optimizer, Notification, Analytics.
- Derive each card's state from the logs (which `agent` has logged) → pending / running / done + spinner.

### C4. Live log feed
- Render `logs` newest-last; color `error` logs red. Auto-scroll.

### C5. Map panel (Leaflet)
- `react-leaflet` `<MapContainer>` with OpenStreetMap tiles.
- For each zone, draw a `<Polyline>` from the route `geometry` (GeoJSON `LineString` → flip `[lng,lat]` to `[lat,lng]`), one color per zone, plus markers for each stop.
- **Note:** import the map with `dynamic(() => ..., { ssr: false })` (Leaflet needs the browser).

### C6. Analytics panel (Recharts)
- Bar/again chart: naive vs optimised km; cards for CO₂, cost ₹, time saved.

### C7. Final report card
- When `completed`, show `savings_km`, `savings_pct`, `co2_avoided_kg`, `cost_saved_inr`, `on_time_rate`, `trees_equivalent`.
- ✅ **Done when:** a mock run animates cards → logs → map → report.

---

## PART D — Mock data (so you don't wait on backend)
- Create `frontend/mock/run.json` matching `ARCHITECTURE.md` (a run + logs + routes with `geometry` + analytics).
- Point the polling fetch at the mock during development, swap to the real API later.
- ✅ **Done when:** the whole dashboard renders from the mock file.

## PART E — Deploy to Vercel
- **E1.** Push `frontend/` to GitHub; import the repo in vercel.com.
- **E2.** Set `NEXT_PUBLIC_API_URL` = the Railway backend URL (get it from Sameer).
- **E3.** Redeploy; open the live URL.
- **E4.** Tell Sameer your Vercel URL so he can add it to backend CORS.
- ✅ **Done when:** the deployed site runs a real end-to-end run.

---

### Your overall Definition of Done
On the live Vercel URL: paste sample addresses → agents light up live → the map draws real road routes → the impact report appears. (You also present this on stage — rehearse with `docs/DEMO_SCRIPT.md`.)
