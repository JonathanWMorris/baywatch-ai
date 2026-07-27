import {useEffect, useState} from "react";
import {
  createComplianceReport,
  dispatchRescueDrone,
  dropDroneBuoy,
  executeShiftRotation,
  getComplianceIncidents,
  getDroneStatus,
  getMeshStatus,
  getShiftStatus,
  getSirenStatus,
  getThermalStatus,
  getTowers,
  setThermalConfig,
  triggerSirenAlarm,
} from "../services/api";
import type {
  Drone,
  IncidentReport,
  MeshNode,
  ShiftStatus,
  SirenStatus,
  ThermalStatus,
  Tower,
} from "../types";

interface ProductionSuitePanelProps {
  onRefreshParent: () => void;
}

export function ProductionSuitePanel({onRefreshParent}: ProductionSuitePanelProps) {
  const [activeTab, setActiveTab] = useState<"towers" | "drone" | "thermal" | "mesh" | "compliance" | "siren" | "shift">("towers");

  const [towers, setTowers] = useState<Tower[]>([]);
  const [drones, setDrones] = useState<Drone[]>([]);
  const [thermal, setThermal] = useState<ThermalStatus | null>(null);
  const [meshNodes, setMeshNodes] = useState<MeshNode[]>([]);
  const [incidents, setIncidents] = useState<IncidentReport[]>([]);
  const [siren, setSiren] = useState<SirenStatus | null>(null);
  const [shift, setShift] = useState<ShiftStatus | null>(null);

  const [toastMsg, setToastMsg] = useState<string | null>(null);

  const fetchAllSuiteData = async () => {
    try {
      const [tRes, dRes, thRes, mRes, cRes, sRes, shRes] = await Promise.all([
        getTowers(),
        getDroneStatus(),
        getThermalStatus(),
        getMeshStatus(),
        getComplianceIncidents(),
        getSirenStatus(),
        getShiftStatus(),
      ]);
      setTowers(tRes.towers);
      setDrones(dRes.drones);
      setThermal(thRes);
      setMeshNodes(mRes.nodes);
      setIncidents(cRes.incidents);
      setSiren(sRes);
      setShift(shRes.shift);
    } catch {
      // Graceful fallback
    }
  };

  useEffect(() => {
    fetchAllSuiteData();
    const interval = setInterval(fetchAllSuiteData, 5000);
    return () => clearInterval(interval);
  }, []);

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  return (
    <section className="suite-panel-container">
      <div className="suite-panel-header">
        <div className="suite-badge">
          <span className="suite-icon">🛡️</span>
          <div>
            <h3>Production Lifeguard Agency Operations Suite</h3>
            <p>Multi-Tower Grid · Autonomous UAV · Thermal IR · Off-Grid Mesh · Legal Audit · Tower Sirens</p>
          </div>
        </div>

        <div className="suite-nav-tabs">
          <button className={activeTab === "towers" ? "active" : ""} onClick={() => setActiveTab("towers")}>
            🗼 Tower Grid ({towers.length})
          </button>
          <button className={activeTab === "drone" ? "active" : ""} onClick={() => setActiveTab("drone")}>
            🛸 UAV Drone ({drones.length})
          </button>
          <button className={activeTab === "thermal" ? "active" : ""} onClick={() => setActiveTab("thermal")}>
            🔥 Thermal IR
          </button>
          <button className={activeTab === "mesh" ? "active" : ""} onClick={() => setActiveTab("mesh")}>
            📡 Off-Grid Mesh
          </button>
          <button className={activeTab === "compliance" ? "active" : ""} onClick={() => setActiveTab("compliance")}>
            📋 Legal Audit
          </button>
          <button className={activeTab === "siren" ? "active" : ""} onClick={() => setActiveTab("siren")}>
            🚨 Tower Sirens
          </button>
          <button className={activeTab === "shift" ? "active" : ""} onClick={() => setActiveTab("shift")}>
            ⏱️ Shift Rotation
          </button>
        </div>
      </div>

      <div className="suite-panel-body">
        {toastMsg && <div className="suite-toast">{toastMsg}</div>}

        {/* 1. TOWER GRID TAB */}
        {activeTab === "towers" && (
          <div className="suite-tab-content">
            <h4>Multi-Tower Sector Grid & Geofenced Routing</h4>
            <div className="towers-grid">
              {towers.map((t) => (
                <div key={t.tower_id} className={`tower-card risk-${t.risk_level}`}>
                  <div className="tower-card-head">
                    <strong>{t.name}</strong>
                    <span className={`risk-pill ${t.risk_level}`}>{t.risk_level.toUpperCase()}</span>
                  </div>
                  <p className="tower-zone">{t.zone} · Assigned: <strong>{t.assigned_guard}</strong></p>
                  <div className="tower-video-preview">
                    <iframe src={t.embed_url} title={t.name} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 2. AUTONOMOUS RESCUE DRONE TAB */}
        {activeTab === "drone" && (
          <div className="suite-tab-content">
            <h4>MAVLink Autonomous Rescue UAV Dispatch & Buoy Drop</h4>
            {drones.map((d) => (
              <div key={d.drone_id} className="drone-card">
                <div className="drone-head">
                  <div>
                    <h5>{d.model} ({d.drone_id})</h5>
                    <span className="drone-status-tag">Status: <strong>{d.status.toUpperCase()}</strong></span>
                  </div>
                  <span className="battery-badge">Battery: {d.battery_pct}%</span>
                </div>

                <div className="drone-details">
                  <p>Payload: <strong>{d.payload_status === "buoy_attached" ? "Self-Inflating Flotation Buoy Attached" : "Buoy Released at Target"}</strong></p>
                  {d.last_mission && (
                    <p className="mission-note">Last Mission: Dispatched to {d.last_mission.target_zone} ({d.last_mission.coordinates})</p>
                  )}
                </div>

                <div className="drone-actions">
                  <button
                    className="drone-btn primary"
                    onClick={async () => {
                      showToast("Launching Autonomous Drone to Zone 3...");
                      await dispatchRescueDrone(d.drone_id, 26.3152, -80.0758, "Zone 3 (South Sandbar)");
                      await fetchAllSuiteData();
                      onRefreshParent();
                    }}
                  >
                    🚀 Launch UAV to Swimmer (Zone 3)
                  </button>
                  <button
                    className="drone-btn warning"
                    onClick={async () => {
                      showToast("Dropping self-inflating buoy!");
                      await dropDroneBuoy(d.drone_id);
                      await fetchAllSuiteData();
                      onRefreshParent();
                    }}
                  >
                    🛟 Drop Flotation Buoy
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 3. THERMAL IR TAB */}
        {activeTab === "thermal" && (
          <div className="suite-tab-content">
            <h4>Long-Wave Infrared (LWIR) Thermal Night Vision</h4>
            <div className="thermal-controls-card">
              <div className="thermal-status-row">
                <span>Thermal Sensor: <strong>{thermal?.sensor}</strong></span>
                <span>Heat Signatures Tracked: <strong>{thermal?.heat_signatures_detected} Swimmers</strong></span>
              </div>

              <div className="thermal-toggle-row">
                <label className="toggle-label">
                  <input
                    type="checkbox"
                    checked={thermal?.enabled ?? false}
                    onChange={async (e) => {
                      await setThermalConfig(e.target.checked);
                      await fetchAllSuiteData();
                    }}
                  />
                  Enable Thermal Night Vision Stream Overlay
                </label>
              </div>

              <div className="palette-buttons">
                {["ironbow", "plasma", "white_hot", "night_vision"].map((p) => (
                  <button
                    key={p}
                    className={`palette-btn ${thermal?.palette === p ? "active" : ""}`}
                    onClick={async () => {
                      await setThermalConfig(true, p);
                      await fetchAllSuiteData();
                    }}
                  >
                    {p.replace("_", " ").toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 4. OFF-GRID MESH TAB */}
        {activeTab === "mesh" && (
          <div className="suite-tab-content">
            <h4>Off-Grid 915 MHz LoRa & Meshtastic Emergency Mesh</h4>
            <div className="mesh-nodes-grid">
              {meshNodes.map((n) => (
                <div key={n.node_id} className="mesh-node-card">
                  <div className="node-head">
                    <strong>{n.name}</strong>
                    <span className="freq-tag">{n.frequency}</span>
                  </div>
                  <div className="node-stats">
                    <span>Hops: {n.hops}</span>
                    <span>SNR: {n.snr_db} dB</span>
                    <span>Battery: {n.battery_pct}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 5. LEGAL COMPLIANCE TAB */}
        {activeTab === "compliance" && (
          <div className="suite-tab-content">
            <h4>Automated Legal & Incident Compliance Logger</h4>
            <div className="incidents-list">
              {incidents.map((i) => (
                <div key={i.incident_id} className="incident-card">
                  <div className="incident-head">
                    <div>
                      <strong>{i.incident_id} · {i.incident_type}</strong>
                      <p>{i.zone} · Guard: {i.guard_signoff}</p>
                    </div>
                    <a
                      href={`http://localhost:8001/api/compliance/export/${i.incident_id}`}
                      target="_blank"
                      rel="noreferrer"
                      className="export-btn"
                    >
                      📥 Download Audit Log
                    </a>
                  </div>
                  <p className="evidence-preview">{i.evidence_summary}</p>
                </div>
              ))}
            </div>
            <button
              className="create-report-btn"
              onClick={async () => {
                showToast("Generating legal compliance audit log...");
                await createComplianceReport("Zone 3 (South Sandbar)", "Rip Current Rescue Assist", "high", "Swimmer submerged >18s logged via IoT buoy.", "Guard Jordan");
                await fetchAllSuiteData();
                onRefreshParent();
              }}
            >
              ➕ File New Compliance Incident Audit Log
            </button>
          </div>
        )}

        {/* 6. TOWER SIRENS TAB */}
        {activeTab === "siren" && (
          <div className="suite-tab-content">
            <h4>Physical Beach Tower Sirens & High-Intensity Strobes</h4>
            <div className="siren-card">
              <div className="siren-status-display">
                <span>Strobe Relay: <strong className={siren?.strobe_active ? "active-text" : ""}>{siren?.strobe_active ? "FLASHING" : "STANDBY"}</strong></span>
                <span>Siren Horn: <strong className={siren?.siren_active ? "active-text" : ""}>{siren?.siren_active ? "ACTIVE SIREN" : "SILENT"}</strong></span>
              </div>

              <div className="siren-actions">
                <button
                  className="siren-btn danger"
                  onClick={async () => {
                    showToast("ACTIVATING BEACH EVACUATION SIREN!");
                    await triggerSirenAlarm("evacuate_beach", "Guard Jordan");
                    await fetchAllSuiteData();
                    onRefreshParent();
                  }}
                >
                  🚨 TRIGGER BEACH EVACUATION SIREN
                </button>

                <button
                  className="siren-btn warning"
                  onClick={async () => {
                    showToast("Flashing warning strobes...");
                    await triggerSirenAlarm("warning_strobe", "Guard Jordan");
                    await fetchAllSuiteData();
                    onRefreshParent();
                  }}
                >
                  ⚡ Flash Warning Strobes Only
                </button>

                <button
                  className="siren-btn secondary"
                  onClick={async () => {
                    showToast("Sirens reset to standby.");
                    await triggerSirenAlarm("standby", "Guard Jordan");
                    await fetchAllSuiteData();
                    onRefreshParent();
                  }}
                >
                  Reset to Standby
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 7. SHIFT HANDOVER TAB */}
        {activeTab === "shift" && (
          <div className="suite-tab-content">
            <h4>Guard Vigilance Rotation & Shift Handover</h4>
            {shift && (
              <div className="shift-card">
                <div className="shift-head">
                  <div>
                    <h5>Shift ID: {shift.shift_id} · Tower 1</h5>
                    <p>Current Guard: <strong>{shift.current_guard}</strong> $\rightarrow$ Incoming Guard: <strong>{shift.incoming_guard}</strong></p>
                  </div>
                  <div className="rotation-timer">
                    <span className="timer-val">{Math.floor(shift.seconds_remaining_in_rotation / 60)}m {shift.seconds_remaining_in_rotation % 60}s</span>
                    <small>Rotation Timer</small>
                  </div>
                </div>

                <p className="handover-notes">Notes: “{shift.handover_notes}”</p>

                <button
                  className="rotate-btn"
                  onClick={async () => {
                    showToast("Shift rotation logged!");
                    await executeShiftRotation("Guard Sarah", "Tower rotation completed cleanly.");
                    await fetchAllSuiteData();
                    onRefreshParent();
                  }}
                >
                  🔄 Complete Shift Handover Rotation
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
