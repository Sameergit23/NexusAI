"use client";

import { Fragment } from "react";
import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { Zone } from "@/lib/api";

const COLORS = ["#6366f1", "#4f46e5", "#10b981", "#f59e0b", "#ef4444", "#ec4899"];

function isZone(v: unknown): v is Zone {
  return typeof v === "object" && v !== null && "geometry" in (v as object);
}

export default function MapView({ routes }: { routes: Record<string, Zone | number> | null }) {
  const zones = routes
    ? Object.entries(routes).filter(([, v]) => isZone(v)) as [string, Zone][]
    : [];

  // Collect all coordinates to center/fit the map.
  const allPts: [number, number][] = [];
  zones.forEach(([, z]) =>
    z.geometry.coordinates.forEach(([lng, lat]) => allPts.push([lat, lng]))
  );
  const center: [number, number] =
    allPts.length > 0
      ? [
          allPts.reduce((s, p) => s + p[0], 0) / allPts.length,
          allPts.reduce((s, p) => s + p[1], 0) / allPts.length,
        ]
      : [18.5204, 73.8567]; // Pune

  return (
    <MapContainer center={center} zoom={12} scrollWheelZoom className="h-full w-full rounded-xl">
      <TileLayer
        attribution='&copy; OpenStreetMap'
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
      />
      {zones.map(([id, z], i) => {
        const color = COLORS[i % COLORS.length];
        const line = z.geometry.coordinates.map(([lng, lat]) => [lat, lng] as [number, number]);
        return (
          <Fragment key={id}>
            <Polyline positions={line} pathOptions={{ color, weight: 4, opacity: 0.85 }} />
            {line.length > 0 && (
              <CircleMarker center={line[0]} radius={6} pathOptions={{ color, fillColor: color, fillOpacity: 1 }}>
                <Tooltip>{`${z.vehicle_id ?? id} start`}</Tooltip>
              </CircleMarker>
            )}
            {line.length > 1 && (
              <CircleMarker
                center={line[line.length - 1]}
                radius={6}
                pathOptions={{ color, fillColor: "#ffffff", fillOpacity: 1 }}
              >
                <Tooltip>{`${z.vehicle_id ?? id} end · ${z.distance_km} km`}</Tooltip>
              </CircleMarker>
            )}
          </Fragment>
        );
      })}
    </MapContainer>
  );
}
