import type {DashboardStatus} from "../types";

// Keep development requests same-origin so Vite can proxy them without browser
// CORS or localhost/127.0.0.1 mismatches. Set VITE_API_URL for hosted builds.
export const API = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

async function json<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API}${url}`, init);
  } catch {
    throw new Error(
      "Cannot reach the Baywatch API. Confirm Flask is running on port 8001.",
    );
  }
  const body = await response.json();
  if (!response.ok) throw new Error(body.error ?? `Request failed (${response.status})`);
  return body as T;
}

export const getStatus = () => json<DashboardStatus>("/api/status");
export const startLiveAnalysis = () => json("/api/live/start", {method: "POST"});
export const stopLiveAnalysis = () => json("/api/live/stop", {method: "POST"});
export const acknowledgeAlert = (id: string) => json(`/api/alerts/${id}/acknowledge`, {method: "POST"});
export const logAnnouncement = (message: string, cameraId?: string) => json("/api/warnings/announce", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({message, camera_id: cameraId})});
export const simulateEmergency = (cameraId: string) => json("/api/emergency/escalate", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({camera_id: cameraId, confirmed: true})});
