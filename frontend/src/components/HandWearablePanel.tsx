import {useEffect, useState} from "react";
import {getHandDevices, getHandGATTSpec, sendHandGesture, triggerHandHaptic} from "../services/api";
import {bleManager} from "../services/ble";
import type {GATTSpec, HandDevice} from "../types";

interface HandWearablePanelProps {
  onRefreshParent: () => void;
}

export function HandWearablePanel({onRefreshParent}: HandWearablePanelProps) {
  const [devices, setDevices] = useState<HandDevice[]>([]);
  const [gattSpec, setGattSpec] = useState<GATTSpec | null>(null);
  const [activeTab, setActiveTab] = useState<"hand" | "gatt" | "gestures" | "haptics">("hand");
  const [hapticFeedback, setHapticFeedback] = useState<string | null>(null);
  const [bleConnectedDevice, setBleConnectedDevice] = useState<string | null>(null);
  const [bleConnecting, setBleConnecting] = useState(false);

  const fetchHandData = async () => {
    try {
      const devRes = await getHandDevices();
      setDevices(devRes.devices);
      const specRes = await getHandGATTSpec();
      setGattSpec(specRes);
    } catch {
      // Graceful fallback
    }
  };

  useEffect(() => {
    fetchHandData();
    const interval = setInterval(fetchHandData, 4000);
    return () => clearInterval(interval);
  }, []);

  const connectPhysicalBLE = async () => {
    setBleConnecting(true);
    setHapticFeedback("Scanning for nearby BLE lifeguard hand hardware...");
    try {
      const deviceName = await bleManager.connect(
        (_buffer) => {
          // Live BLE Telemetry notification callback
          setHapticFeedback("Received live BLE telemetry notification from physical hardware!");
          fetchHandData();
        },
        (gestureCode) => {
          // Live BLE Gesture notification callback
          const gestureMap: Record<number, string> = {
            1: "PALM_SQUEEZE_SOS",
            2: "DOUBLE_TAP_WHISTLE",
            3: "WAVE_ACKNOWLEDGE",
          };
          const gestureName = gestureMap[gestureCode] || "UNKNOWN";
          handleGestureClick(devices[0]?.device_id || "HAND-GUARD-01", gestureName);
        },
      );
      setBleConnectedDevice(deviceName);
      setHapticFeedback(`Paired with BLE Hardware: ${deviceName}`);
    } catch (err) {
      setHapticFeedback(err instanceof Error ? err.message : "BLE connection failed");
    }
    setBleConnecting(false);
  };

  const handleGestureClick = async (deviceId: string, gestureCode: string) => {
    setHapticFeedback(`Triggering ${gestureCode}...`);
    try {
      const res = await sendHandGesture(deviceId, gestureCode);
      if (res.success) {
        setHapticFeedback(`Gesture Action: ${res.action}`);
        await fetchHandData();
        onRefreshParent();
      }
    } catch (err) {
      setHapticFeedback(err instanceof Error ? err.message : "Gesture failed");
    }
    setTimeout(() => setHapticFeedback(null), 3000);
  };

  const handleHapticTrigger = async (deviceId: string, patternId: string) => {
    setHapticFeedback(`Sending haptic command '${patternId}'...`);
    try {
      const res = await triggerHandHaptic(deviceId, patternId);
      if (res.success) {
        setHapticFeedback(res.message);
        await fetchHandData();
      }
    } catch (err) {
      setHapticFeedback(err instanceof Error ? err.message : "Haptic trigger failed");
    }
    setTimeout(() => setHapticFeedback(null), 3000);
  };

  const device = devices[0];

  return (
    <section className="hand-panel-container">
      <div className="hand-panel-header">
        <div className="hand-badge">
          <span className="hand-icon">✋</span>
          <div>
            <h3>Lifeguard Hand Embedded Hardware API</h3>
            <p>Tactile Glove / Palm Sensor & BLE GATT Profile Specification</p>
          </div>
        </div>

        <div className="hand-nav-tabs">
          <button
            className={`ble-connect-btn ${bleConnectedDevice ? "connected" : ""}`}
            onClick={connectPhysicalBLE}
            disabled={bleConnecting}
          >
            {bleConnecting ? "Scanning BLE…" : bleConnectedDevice ? `🔗 Paired: ${bleConnectedDevice}` : "📶 Pair Physical BLE Hardware"}
          </button>
          <button className={activeTab === "hand" ? "active" : ""} onClick={() => setActiveTab("hand")}>
            Hand Hardware
          </button>
          <button className={activeTab === "gestures" ? "active" : ""} onClick={() => setActiveTab("gestures")}>
            Palm Gestures
          </button>
          <button className={activeTab === "haptics" ? "active" : ""} onClick={() => setActiveTab("haptics")}>
            Hand Haptics
          </button>
          <button className={activeTab === "gatt" ? "active" : ""} onClick={() => setActiveTab("gatt")}>
            BLE GATT & C Header
          </button>
        </div>
      </div>

      <div className="hand-panel-body">
        {/* TACTICAL GLOVE / HAND DEVICE GRAPHICAL SIMULATOR */}
        <div className="hand-device-simulator">
          <div className="tactical-glove-frame">
            <div className="glove-palm-sensor">
              <span className="sensor-ring pulse"></span>
              <strong className="palm-label">HYDROSTATIC DEPTH SENSOR</strong>
              <small>{device?.depth_hpa ?? 1013} hPa (Sea Level)</small>
            </div>

            <div className="glove-knuckle-haptic">
              <span className="haptic-motor-icon">⚡</span>
              <strong className="motor-label">LRA HAPTIC MOTOR</strong>
              <small>Last Sent: {device?.last_haptic_sent ?? "HAPTIC_PATTERN_TICK"}</small>
            </div>

            <div className="glove-wrist-unit">
              <div className="wrist-status-row">
                <span>Guard: <strong>{device?.guard_name ?? "Guard Jordan"}</strong></span>
                <span>RSSI: <strong>{device?.signal_rssi_dbm ?? -52} dBm</strong></span>
              </div>
              <div className="wrist-vitals-row">
                <span>Heart Rate: <strong>{device?.heart_rate_bpm ?? 76} BPM</strong></span>
                <span>Motion: <strong>{device?.motion_state ?? "PATROL"}</strong></span>
              </div>
            </div>
          </div>
        </div>

        {/* TAB CONTROLS AND DETAILS */}
        <div className="hand-controls-area">
          {hapticFeedback && <div className="hand-feedback-toast">{hapticFeedback}</div>}

          {activeTab === "hand" && (
            <div className="hand-tab-content">
              <h4>Hardened Marine Hand Device Architecture</h4>
              <p>
                Lifeguards wear IP68 waterproof tactical gloves or palm-mounted silicone bands equipped with:
              </p>
              <ul className="hand-features-list">
                <li>
                  <strong>Hydrostatic Pressure Sensor:</strong> Measures millimeter-level water submersion depth (hPa) to detect drowning without false alarms.
                </li>
                <li>
                  <strong>Dual LRA Haptic Actuator:</strong> Delivers sharp tactile pulse patterns directly to the lifeguard's palm or wrist skin.
                </li>
                <li>
                  <strong>Emergency Palm Squeeze Switch:</strong> A tactile pressure switch inside the palm that lets the guard trigger a panic SOS while swimming or rescuing.
                </li>
              </ul>
            </div>
          )}

          {activeTab === "gestures" && (
            <div className="hand-tab-content">
              <h4>Palm & Hand Gesture Controls</h4>
              <p>Execute instant commands without looking at a screen:</p>

              <div className="gesture-grid">
                <button
                  className="gesture-tile emergency"
                  onClick={() => handleGestureClick(device?.device_id || "HAND-GUARD-01", "PALM_SQUEEZE_SOS")}
                >
                  <span className="gesture-icon">✊</span>
                  <strong>Palm Squeeze SOS</strong>
                  <small>Triggers Emergency Call 911 Simulation</small>
                </button>

                <button
                  className="gesture-tile warning"
                  onClick={() => handleGestureClick(device?.device_id || "HAND-GUARD-01", "DOUBLE_TAP_WHISTLE")}
                >
                  <span className="gesture-icon">✌️</span>
                  <strong>Double-Tap Whistle</strong>
                  <small>Broadcasts Warning Whistle & Audio</small>
                </button>

                <button
                  className="gesture-tile primary"
                  onClick={() => handleGestureClick(device?.device_id || "HAND-GUARD-01", "WAVE_ACKNOWLEDGE")}
                >
                  <span className="gesture-icon">👋</span>
                  <strong>Hand Wave Acknowledge</strong>
                  <small>Clears Active Alert Notification</small>
                </button>
              </div>
            </div>
          )}

          {activeTab === "haptics" && (
            <div className="hand-tab-content">
              <h4>Hand Haptic Actuator Commands</h4>
              <p>Transmit tactile vibration vectors to the lifeguard's hand motor:</p>

              <div className="haptic-buttons-grid">
                <button
                  className="haptic-pulse-btn"
                  onClick={() => handleHapticTrigger(device?.device_id || "HAND-GUARD-01", "HAPTIC_PATTERN_TICK")}
                >
                  📳 Single Status Tick
                </button>
                <button
                  className="haptic-pulse-btn warning"
                  onClick={() => handleHapticTrigger(device?.device_id || "HAND-GUARD-01", "HAPTIC_PATTERN_DOUBLE_PULSE")}
                >
                  📳 Double Rip-Current Pulse
                </button>
                <button
                  className="haptic-pulse-btn warning"
                  onClick={() => handleHapticTrigger(device?.device_id || "HAND-GUARD-01", "HAPTIC_PATTERN_WARNING_BURST")}
                >
                  📳 High Warning Burst
                </button>
                <button
                  className="haptic-pulse-btn danger"
                  onClick={() => handleHapticTrigger(device?.device_id || "HAND-GUARD-01", "HAPTIC_PATTERN_SOS_EMERGENCY")}
                >
                  🚨 Emergency SOS Haptic Burst
                </button>
              </div>
            </div>
          )}

          {activeTab === "gatt" && (
            <div className="hand-tab-content">
              <div className="gatt-header">
                <h4>BLE GATT Service & C Header Specification</h4>
                <a
                  href="http://localhost:8001/api/hand-wearable/embedded-header.h"
                  target="_blank"
                  rel="noreferrer"
                  className="c-header-dl-btn"
                >
                  📥 Download C Header (lifeguard_hand_protocol.h)
                </a>
              </div>

              <div className="gatt-details">
                <div className="gatt-meta">
                  <span>Service UUID: <code>{gattSpec?.service_uuid}</code></span>
                </div>

                <div className="code-block-container">
                  <span className="code-label">Packed C Telemetry Struct (7 Bytes):</span>
                  <pre className="code-block">
{`struct __attribute__((packed)) {
    uint16_t depth_hpa;      // Hydrostatic pressure (hPa)
    uint16_t submersion_ms;  // Submersion duration (ms)
    uint8_t  heart_rate;     // Heart rate (BPM)
    uint8_t  battery_pct;    // Battery (0-100%)
    uint8_t  motion_state;   // Motion State (0x01: Patrol, 0x03: Panic Thrash)
};`}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
