export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const AGENTS = [
  "orchestrator",
  "planner",
  "route_optimizer",
  "notification",
  "analytics",
] as const;

export type AgentName = (typeof AGENTS)[number];

export type Vertical = "logistics" | "hr";

export interface Delivery {
  id?: string;
  address: string;
  lat?: number;
  lng?: number;
}

export interface Employee {
  id?: string;
  name: string;
  role?: string;
  team?: string;
  email?: string;
}

export interface LogEntry {
  agent: string;
  message: string;
  level: "info" | "warning" | "error";
  created_at: string;
}

export interface Geometry {
  type: string;
  coordinates: [number, number][];
}

export interface Zone {
  distance_km: number;
  duration_min: number;
  geometry: Geometry;
  ordered_stops: string[];
  vehicle_id?: string;
  status: string;
}

export interface Report {
  naive_km: number;
  optimised_km: number;
  savings_km: number;
  savings_pct: number;
  co2_avoided_kg: number;
  cost_saved_inr: number;
  time_saved_min: number;
  on_time_rate: number;
  trees_equivalent: number;
}

// Shape from docs/hr-onboarding/OVERVIEW.md
export interface HrReport {
  total_hires: number;
  tasks_completed: number;
  tasks_total: number;
  readiness_pct: number;
  hours_saved: number;
  cost_saved_inr: number;
  emails_sent: number;
}

export interface RunResponse {
  run: {
    id: string;
    goal: string;
    status: "running" | "completed" | "failed" | "pending";
    num_vehicles: number;
    vertical?: Vertical;
    created_at: string;
    completed_at: string | null;
  } | null;
  logs: LogEntry[];
  deliveries: Delivery[];
  analytics: Report | null;
  routes: Record<string, Zone | number> | null;
  report: Report | HrReport | null;
}

// Third arg: number of vehicles (logistics, as before) or the vertical "hr".
export async function startRun(
  goal: string,
  items: Delivery[] | Employee[],
  vehiclesOrVertical: number | Vertical = "logistics"
) {
  const body =
    vehiclesOrVertical === "hr"
      ? { vertical: "hr", goal, employees: items as Employee[] }
      : {
          vertical: "logistics",
          goal,
          deliveries: items as Delivery[],
          num_vehicles: typeof vehiclesOrVertical === "number" ? vehiclesOrVertical : 1,
        };
  const res = await fetch(`${API}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`start run failed: ${res.status}`);
  return (await res.json()) as { run_id: string; status: string };
}

export async function getRun(runId: string): Promise<RunResponse> {
  const res = await fetch(`${API}/run/${runId}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`get run failed: ${res.status}`);
  return await res.json();
}

// Pre-geocoded sample so the demo runs fast and reliably (no geocoding wait).
export const SAMPLE_GOAL =
  "Deliver 10 packages across Pune today using 2 vehicles, minimise distance and notify every customer with an ETA";

export const SAMPLE_DELIVERIES: Delivery[] = [
  { id: "1", address: "FC Road, Shivajinagar, Pune", lat: 18.5236, lng: 73.841 },
  { id: "2", address: "Koregaon Park, Pune", lat: 18.5362, lng: 73.8939 },
  { id: "3", address: "Shivajinagar, Pune", lat: 18.5308, lng: 73.8522 },
  { id: "4", address: "Kothrud, Pune", lat: 18.5074, lng: 73.8077 },
  { id: "5", address: "Hadapsar, Pune", lat: 18.5089, lng: 73.926 },
  { id: "6", address: "Viman Nagar, Pune", lat: 18.5679, lng: 73.9143 },
  { id: "7", address: "Aundh, Pune", lat: 18.5589, lng: 73.8077 },
  { id: "8", address: "Pune Camp, Pune", lat: 18.5125, lng: 73.879 },
  { id: "9", address: "Baner, Pune", lat: 18.559, lng: 73.7868 },
  { id: "10", address: "Hinjewadi Phase 1, Pune", lat: 18.5912, lng: 73.7389 },
];

export const SAMPLE_HR_GOAL =
  "Onboard 5 new engineers joining Monday — provision accounts, schedule intro meetings, send welcome packets, track completion";

export const SAMPLE_EMPLOYEES: Employee[] = [
  { id: "1", name: "Priya Sharma",   role: "Backend Engineer",  team: "Platform",  email: "priya@nexusai.demo" },
  { id: "2", name: "Arjun Mehta",    role: "Frontend Engineer", team: "Web",       email: "arjun@nexusai.demo" },
  { id: "3", name: "Riya Nair",      role: "Data Scientist",    team: "ML",        email: "riya@nexusai.demo" },
  { id: "4", name: "Karan Singh",    role: "DevOps Engineer",   team: "Infra",     email: "karan@nexusai.demo" },
  { id: "5", name: "Aanya Iyer",     role: "Product Designer",  team: "Design",    email: "aanya@nexusai.demo" },
];
