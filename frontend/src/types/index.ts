export type RiskLevel = "low" | "moderate" | "high" | "critical" | "unknown";

export interface Camera { id: string; name: string; status: string; risk_level: RiskLevel; media_url: string | null; source_type?: "file" | "youtube"; embed_url?: string; external?: boolean }
export interface HazardEvent { type: string; severity: RiskLevel; description: string; evidence: string[]; confidence: number }
export interface Assessment { camera_id: string; analysis_status: string; risk_level: RiskLevel; events: HazardEvent[]; audio_observations: {type: string; description: string; confidence: number}[]; environment: {risk_level: RiskLevel; factors: string[]; summary: string}; public_warning: string | null; reasoning_summary: string; errors: string[] }
export interface Alert extends HazardEvent { id: string; camera_id: string; acknowledged: boolean; created_at: string }
export interface TimelineEvent { id: string; timestamp: string; category: string; message: string; camera_id?: string; severity?: string; details?: Record<string, unknown> }
export interface Ocean { station_id: string; source: string; wave_height_ft: number | null; dominant_period_sec: number | null; average_period_sec: number | null; wave_direction_deg: number | null; wind_speed_mph: number | null; wind_gust_mph: number | null; water_temp_f: number | null; is_mock: boolean; status_message?: string }
export interface Weather { source: string; temperature_f: number | null; wind_speed_mph: number | null; wind_gust_mph: number | null; wind_direction_deg: number | null; visibility_m: number | null; condition: string; is_mock: boolean; status_message?: string }
export interface OceanRiskAssessment { risk_level: RiskLevel; factors: string[]; summary: string; sources: string[]; source_mode: "live" | "demo"; updated_at: string }
export interface LiveStatus { enabled: boolean; phase: string; video_id: string; watch_url: string; embed_url: string; interval_seconds: number; capture_seconds: number; last_capture: {captured_at?: string; video_frames?: number; audio_seconds?: number} | null; last_assessment: Assessment | null; next_analysis_at: string | null; error: string | null; environment_mode: "sensor_fusion"; dependencies: {ready: boolean; yt_dlp: boolean; av: boolean; python_executable: string; install_command: string} }
export interface DashboardStatus { global_status: string; cameras: Camera[]; assessments: Record<string, Assessment>; alerts: Alert[]; events: TimelineEvent[]; warning: {camera_id?: string; message: string; issued: boolean} | null; escalation: {camera_id: string; severity: string; reason: string} | null; ocean: Ocean; weather: Weather; ocean_risk_assessment: OceanRiskAssessment; gemma: {loaded: boolean; device: string; error?: string}; live: LiveStatus }

export interface HapticProfile { pattern: number[]; intensity: string; label: string; description: string }
export interface WatchQuickAction { id: string; label: string; icon: string; enabled: boolean; alert_id?: string; danger?: boolean }
export interface WatchStatus { timestamp: string; device_target: string; global_status: string; risk_level: RiskLevel; active_alerts_count: number; latest_alert: Alert | null; haptic_profile: HapticProfile; ocean_summary: { wave_height: string; water_temp: string; wind_speed: string; sources: string[] }; quick_actions: WatchQuickAction[]; warning_draft?: { camera_id?: string; message: string; issued: boolean } | null; escalation_status?: Record<string, unknown> | null }

export interface IoTDevice {
  device_id: string;
  name: string;
  device_type: "edge_vision_buoy" | "wearable_submersion_tracker" | "sonar_pod" | "drone_scout";
  zone: string;
  protocol: "lorawan" | "mqtt" | "cellular_nbiot";
  status: string;
  submersion_seconds: number;
  heart_rate_bpm?: number | null;
  battery_pct: number;
  signal_rssi_dbm: number;
  alert_status: "normal" | "submerged_warning" | "drowning_critical" | "heartrate_distress";
  firmware: string;
  last_seen: string;
}

export interface IoTDevicesResponse {
  devices: IoTDevice[];
  telemetry_count: number;
}

export interface HandDevice {
  device_id: string;
  name: string;
  guard_name: string;
  location: string;
  depth_hpa: number;
  submersion_seconds: number;
  heart_rate_bpm: number;
  battery_pct: number;
  motion_state: string;
  last_gesture: string;
  last_haptic_sent: string;
  signal_rssi_dbm: number;
  last_seen: string;
}

export interface GATTSpec {
  service_uuid: string;
  name: string;
  characteristics: Record<string, {
    uuid: string;
    properties: string[];
    byte_format: string;
    c_struct: string;
    description: string;
  }>;
}

export interface Tower {
  tower_id: string;
  name: string;
  zone: string;
  latitude: number;
  longitude: number;
  assigned_guard: string;
  status: string;
  risk_level: RiskLevel;
  camera_feed: string;
  embed_url: string;
}

export interface Drone {
  drone_id: string;
  model: string;
  status: string;
  battery_pct: number;
  payload_status: string;
  current_location: {lat: number; lon: number; altitude_m: number};
  target_location?: {lat: number; lon: number; zone: string} | null;
  last_mission?: {dispatched_at: string; target_zone: string; coordinates: string} | null;
}

export interface ThermalStatus {
  enabled: boolean;
  palette: string;
  contrast: number;
  sensor: string;
  heat_signatures_detected: number;
  water_temp_contrast_delta_c: number;
}

export interface MeshNode {
  node_id: string;
  name: string;
  frequency: string;
  hops: number;
  snr_db: number;
  battery_pct: number;
  status: string;
}

export interface IncidentReport {
  incident_id: string;
  timestamp: string;
  zone: string;
  incident_type: string;
  severity: RiskLevel;
  gemma_confidence: number;
  evidence_summary: string;
  guard_signoff: string;
  legal_status: string;
}

export interface SirenStatus {
  strobe_active: boolean;
  siren_active: boolean;
  mode: string;
  controller: string;
  last_triggered_by?: string | null;
}

export interface ShiftStatus {
  shift_id: string;
  current_guard: string;
  incoming_guard: string;
  tower_id: string;
  rotation_interval_minutes: number;
  seconds_remaining_in_rotation: number;
  vigilance_score: string;
  handover_notes: string;
  last_rotation_time: string;
}




