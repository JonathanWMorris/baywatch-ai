import {useEffect, useState} from "react";
import {getIoTDevices, simulateIoTEvent} from "../services/api";
import type {IoTDevice} from "../types";

interface IoTPanelProps {
  onRefreshParent: () => void;
}

export function IoTPanel({onRefreshParent}: IoTPanelProps) {
  const [devices, setDevices] = useState<IoTDevice[]>([]);
  const [loading, setLoading] = useState(false);
  const [simulatingId, setSimulatingId] = useState<string | null>(null);

  const fetchDevices = async () => {
    try {
      const res = await getIoTDevices();
      setDevices(res.devices);
    } catch {
      // Graceful fallback
    }
  };

  useEffect(() => {
    fetchDevices();
    const interval = setInterval(fetchDevices, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSimulate = async (deviceId: string, alertType: string) => {
    setSimulatingId(deviceId);
    try {
      await simulateIoTEvent(deviceId, alertType);
      await fetchDevices();
      onRefreshParent();
    } catch {
      // Graceful fallback
    }
    setSimulatingId(null);
  };

  return (
    <section className="iot-panel-container">
      <div className="iot-panel-header">
        <div>
          <span className="eyebrow">Hardened Marine Embedded IoT & Edge Mesh</span>
          <h2>Lifeguard Hardware Sensor Nodes</h2>
          <p>
            Real-time telemetry ingested from Edge AI Camera Buoys (NVIDIA Jetson / ESP32-S3),
            Wearable Submersion Wristbands (WAVE DDS), and Subsurface Sonar Pods over LoRaWAN and MQTT.
          </p>
        </div>
        <div className="iot-protocol-chips">
          <span className="protocol-chip lorawan">LoRaWAN LPWAN</span>
          <span className="protocol-chip mqtt">MQTT Broker</span>
          <span className="protocol-chip nbiot">Cellular NB-IoT</span>
        </div>
      </div>

      <div className="iot-devices-grid">
        {devices.map(device => {
          const isCritical = device.alert_status === "drowning_critical";
          const isWarning = device.alert_status === "submerged_warning";

          return (
            <div
              key={device.device_id}
              className={`iot-device-card ${isCritical ? "critical" : isWarning ? "warning" : "normal"}`}
            >
              <div className="device-card-head">
                <div className="device-icon-title">
                  <span className="device-type-icon">
                    {device.device_type === "edge_vision_buoy"
                      ? "⚓"
                      : device.device_type === "wearable_submersion_tracker"
                      ? "⌚"
                      : device.device_type === "sonar_pod"
                      ? "🌊"
                      : "🛸"}
                  </span>
                  <div>
                    <h4>{device.name}</h4>
                    <span className="device-id-tag">{device.device_id} · {device.zone}</span>
                  </div>
                </div>
                <span className={`status-pill ${device.alert_status}`}>
                  {device.alert_status.replace("_", " ").toUpperCase()}
                </span>
              </div>

              <div className="device-stats-row">
                <div className="stat-box">
                  <span className="stat-label">Submersion</span>
                  <strong className={`stat-val ${device.submersion_seconds > 15 ? "danger-text" : ""}`}>
                    {device.submersion_seconds.toFixed(1)}s
                  </strong>
                </div>
                {device.heart_rate_bpm !== undefined && (
                  <div className="stat-box">
                    <span className="stat-label">Pulse</span>
                    <strong className="stat-val">{device.heart_rate_bpm ? `${device.heart_rate_bpm} BPM` : "N/A"}</strong>
                  </div>
                )}
                <div className="stat-box">
                  <span className="stat-label">Battery</span>
                  <strong className="stat-val">{device.battery_pct}%</strong>
                </div>
                <div className="stat-box">
                  <span className="stat-label">Signal</span>
                  <strong className="stat-val">{device.signal_rssi_dbm} dBm</strong>
                </div>
              </div>

              <div className="device-card-foot">
                <div className="firmware-tag">
                  <span>Protocol: <strong>{device.protocol.toUpperCase()}</strong></span>
                  <span>Firmware: <code>{device.firmware}</code></span>
                </div>
                <div className="device-actions">
                  <button
                    className="sim-btn warning"
                    disabled={simulatingId === device.device_id}
                    onClick={() => handleSimulate(device.device_id, "submerged_warning")}
                  >
                    Simulate Warning
                  </button>
                  <button
                    className="sim-btn danger"
                    disabled={simulatingId === device.device_id}
                    onClick={() => handleSimulate(device.device_id, "drowning_critical")}
                  >
                    Simulate Drowning SOS
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
