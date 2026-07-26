import type { DashboardStatus, Scenario } from "../types";

export const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function json<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${url}`, init);
  const body = await response.json();
  if (!response.ok) throw new Error(body.error ?? `Request failed (${response.status})`);
  return body as T;
}

export const getStatus = () => json<DashboardStatus>("/api/status");
export const getScenarios = () => json<Scenario[]>("/api/demo/scenarios");
export const acknowledgeAlert = (id: string) => json(`/api/alerts/${id}/acknowledge`, {method: "POST"});
export const startScenario = (id: string) => json<Scenario>(`/api/demo/scenarios/${id}/start`, {method: "POST"});
export const analyzeMedia = (cameraId: string, video?: File, audio?: File) => {
  const form = new FormData();
  form.set("camera_id", cameraId);
  if (video) form.set("video", video);
  if (audio) form.set("audio", audio);
  return json<{assessment: unknown}>("/api/analyze", {method: "POST", body: form});
};
export const logAnnouncement = (message: string, cameraId?: string) => json("/api/warnings/announce", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({message, camera_id: cameraId})});
export const simulateEmergency = (cameraId: string) => json("/api/emergency/escalate", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({camera_id: cameraId, confirmed: true})});
