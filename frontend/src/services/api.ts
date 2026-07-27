import type {
  DashboardStatus,
  Drone,
  GATTSpec,
  HandDevice,
  IncidentReport,
  IoTDevicesResponse,
  MeshNode,
  ShiftStatus,
  SirenStatus,
  ThermalStatus,
  Tower,
  WatchStatus,
} from "../types";

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

export const getWatchStatus = () => json<WatchStatus>("/api/watch/status");
export const sendWatchAction = (action: string, alertId?: string, details?: Record<string, unknown>, cameraId?: string) =>
  json<{success: boolean; message?: string; error?: string}>("/api/watch/action", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({action, alert_id: alertId, details, camera_id: cameraId}),
  });
export const getWatchHaptics = () => json<{haptic_profiles: Record<string, unknown>}>("/api/watch/haptics");

export const getIoTDevices = () => json<IoTDevicesResponse>("/api/iot/devices");
export const simulateIoTEvent = (deviceId: string, alertType: string) =>
  json<{status: string}>("/api/iot/simulate", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({device_id: deviceId, alert_type: alertType}),
  });

export const getHandDevices = () => json<{devices: HandDevice[]}>("/api/hand-wearable/devices");
export const getHandGATTSpec = () => json<GATTSpec>("/api/hand-wearable/gatt-spec");
export const triggerHandHaptic = (deviceId: string, patternId: string) =>
  json<{success: boolean; message: string}>("/api/hand-wearable/haptic-trigger", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({device_id: deviceId, pattern_id: patternId}),
  });
export const sendHandGesture = (deviceId: string, gestureCode: string) =>
  json<{success: boolean; action?: string}>("/api/hand-wearable/gesture-action", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({device_id: deviceId, gesture_code: gestureCode}),
  });

// 1. Multi-Tower Grid
export const getTowers = () => json<{towers: Tower[]}>("/api/towers");
export const updateTowerRisk = (towerId: string, riskLevel: string) =>
  json<Tower>(`/api/towers/${towerId}/risk`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({risk_level: riskLevel}),
  });

// 2. Autonomous Rescue Drone
export const getDroneStatus = () => json<{drones: Drone[]}>("/api/drone/status");
export const dispatchRescueDrone = (droneId: string, lat: number, lon: number, zone: string) =>
  json<{success: boolean; message: string}>("/api/drone/dispatch", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({drone_id: droneId, latitude: lat, longitude: lon, zone}),
  });
export const dropDroneBuoy = (droneId: string) =>
  json<{success: boolean; message: string}>("/api/drone/drop-buoy", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({drone_id: droneId}),
  });

// 3. Thermal IR Night Vision Mode
export const getThermalStatus = () => json<ThermalStatus>("/api/thermal/status");
export const setThermalConfig = (enabled: boolean, palette?: string, contrast?: number) =>
  json<ThermalStatus>("/api/thermal/config", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({enabled, palette, contrast}),
  });

// 4. Off-Grid Mesh Networks
export const getMeshStatus = () => json<{mesh_active: boolean; nodes: MeshNode[]}>("/api/mesh/status");

// 5. Automated Legal & Incident Compliance Logger
export const getComplianceIncidents = () => json<{incidents: IncidentReport[]}>("/api/compliance/incidents");
export const createComplianceReport = (zone: string, incidentType: string, severity: string, evidence: string, guardName: string) =>
  json<IncidentReport>("/api/compliance/report", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({zone, incident_type: incidentType, severity, evidence, guard_name: guardName}),
  });

// 6. Physical Siren & Strobe Relays
export const getSirenStatus = () => json<SirenStatus>("/api/siren/status");
export const triggerSirenAlarm = (mode: string, operator: string) =>
  json<SirenStatus>("/api/siren/trigger", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({mode, operator}),
  });

// 7. Shift Handover & Vigilance Rotation
export const getShiftStatus = () => json<{shift: ShiftStatus}>("/api/handover/status");
export const executeShiftRotation = (incomingGuard: string, notes: string) =>
  json<{success: boolean; shift: ShiftStatus}>("/api/handover/rotate", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({incoming_guard: incomingGuard, notes}),
  });




