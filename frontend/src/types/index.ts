export type RiskLevel = "low" | "moderate" | "high" | "critical" | "unknown";

export interface Camera { id: string; name: string; status: string; risk_level: RiskLevel; media_url: string | null }
export interface HazardEvent { type: string; severity: RiskLevel; description: string; evidence: string[]; confidence: number }
export interface Assessment { camera_id: string; analysis_status: string; risk_level: RiskLevel; events: HazardEvent[]; audio_observations: {type: string; description: string; confidence: number}[]; environment: {risk_level: RiskLevel; factors: string[]; summary: string}; public_warning: string | null; reasoning_summary: string; errors: string[] }
export interface Alert extends HazardEvent { id: string; camera_id: string; acknowledged: boolean; created_at: string }
export interface TimelineEvent { id: string; timestamp: string; category: string; message: string; camera_id?: string; severity?: string; details?: Record<string, unknown> }
export interface Ocean { station_id: string; source: string; wave_height_ft: number | null; dominant_period_sec: number | null; average_period_sec: number | null; wave_direction_deg: number | null; wind_speed_mph: number | null; wind_gust_mph: number | null; water_temp_f: number | null; is_mock: boolean; status_message?: string }
export interface Weather { source: string; temperature_f: number | null; wind_speed_mph: number | null; wind_gust_mph: number | null; wind_direction_deg: number | null; visibility_m: number | null; condition: string; is_mock: boolean; status_message?: string }
export interface DashboardStatus { global_status: string; cameras: Camera[]; assessments: Record<string, Assessment>; alerts: Alert[]; events: TimelineEvent[]; warning: {camera_id?: string; message: string; issued: boolean} | null; escalation: {camera_id: string; severity: string; reason: string} | null; ocean: Ocean; weather: Weather; gemma: {loaded: boolean; device: string; error?: string} }
export interface Scenario { id: string; name: string; camera_id: string; media_file: string; expected_theme: string; available: boolean; media_url: string | null }

