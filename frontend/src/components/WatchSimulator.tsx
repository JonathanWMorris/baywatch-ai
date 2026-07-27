import {useEffect, useState} from "react";
import {getWatchStatus, sendWatchAction} from "../services/api";
import type {WatchStatus} from "../types";

interface WatchSimulatorProps {
  onRefreshParent: () => void;
}

export function WatchSimulator({onRefreshParent}: WatchSimulatorProps) {
  const [watchData, setWatchData] = useState<WatchStatus | null>(null);
  const [activeTab, setActiveTab] = useState<"face" | "alert" | "actions" | "haptics">("face");
  const [hapticActive, setHapticActive] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState<string>(new Date().toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"}));

  const fetchWatch = async () => {
    try {
      const data = await getWatchStatus();
      setWatchData(data);
      if (data.latest_alert && activeTab === "face") {
        setActiveTab("alert");
      }
    } catch {
      // Graceful fallback
    }
  };

  useEffect(() => {
    fetchWatch();
    const interval = setInterval(fetchWatch, 4000);
    const clockInterval = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"}));
    }, 1000);
    return () => {
      clearInterval(interval);
      clearInterval(clockInterval);
    };
  }, []);

  const triggerHapticVibration = (pattern: number[]) => {
    setHapticActive(true);
    if ("vibrate" in navigator) {
      try {
        navigator.vibrate(pattern);
      } catch {
        // Ignored if browser blocks without gesture
      }
    }

    // Audio frequency click/buzz fallback for demonstration
    try {
      const AudioCtx = window.AudioContext || (window as unknown as {webkitAudioContext: typeof AudioContext}).webkitAudioContext;
      if (AudioCtx) {
        const ctx = new AudioCtx();
        pattern.forEach((duration, i) => {
          if (i % 2 === 0) {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = "sawtooth";
            osc.frequency.setValueAtTime(150, ctx.currentTime);
            gain.gain.setValueAtTime(0.08, ctx.currentTime);
            const startTime = pattern.slice(0, i).reduce((a, b) => a + b, 0) / 1000;
            osc.connect(gain).connect(ctx.destination);
            osc.start(ctx.currentTime + startTime);
            osc.stop(ctx.currentTime + startTime + duration / 1000);
          }
        });
      }
    } catch {
      // Audio synth optional
    }

    setTimeout(() => setHapticActive(false), 1200);
  };

  const handleWristAction = async (actionId: string, alertId?: string) => {
    setActionFeedback(`Executing ${actionId.replace("_", " ")}...`);
    try {
      const res = await sendWatchAction(actionId, alertId);
      if (res.success) {
        setActionFeedback(res.message || "Done");
        if (watchData?.haptic_profile.pattern) {
          triggerHapticVibration(watchData.haptic_profile.pattern);
        }
        await fetchWatch();
        onRefreshParent();
      } else {
        setActionFeedback(res.error || "Action failed");
      }
    } catch (err) {
      setActionFeedback(err instanceof Error ? err.message : "Error");
    }
    setTimeout(() => setActionFeedback(null), 3000);
  };

  const risk = watchData?.risk_level || "low";
  const alert = watchData?.latest_alert;

  return (
    <div className="watch-simulator-container">
      <div className="watch-simulator-header">
        <div className="watch-badge">
          <span className="watch-icon">⌚</span>
          <div>
            <h3>Lifeguard Smartwatch Companion</h3>
            <p>Wear OS / watchOS Wrist Receiver & Haptic Sync</p>
          </div>
        </div>
        <div className="watch-mode-tabs">
          <button className={activeTab === "face" ? "active" : ""} onClick={() => setActiveTab("face")}>
            Watch Face
          </button>
          <button className={activeTab === "alert" ? "active" : ""} onClick={() => setActiveTab("alert")}>
            Wrist Alerts {watchData?.active_alerts_count ? `(${watchData.active_alerts_count})` : ""}
          </button>
          <button className={activeTab === "actions" ? "active" : ""} onClick={() => setActiveTab("actions")}>
            Wrist Actions
          </button>
          <button className={activeTab === "haptics" ? "active" : ""} onClick={() => setActiveTab("haptics")}>
            Haptics
          </button>
        </div>
      </div>

      <div className="watch-simulator-body">
        {/* PHYSICAL SMART WATCH FRAME */}
        <div className={`smartwatch-hardware ${hapticActive ? "haptic-buzzing" : ""}`}>
          <div className="watch-strap-top"></div>

          <div className="watch-case">
            <div className="digital-crown" title="Digital Crown Button"></div>
            <div className="side-button" title="Side Action Button"></div>

            <div className={`watch-screen risk-bg-${risk}`}>
              {/* STATUS BAR */}
              <div className="screen-status-bar">
                <span className="watch-time">{currentTime}</span>
                <span className="watch-status-indicator">
                  <span className={`pulse-dot risk-dot-${risk}`} />
                  {risk.toUpperCase()}
                </span>
              </div>

              {/* SCREEN CONTENT BASED ON TAB */}
              {activeTab === "face" && (
                <div className="watch-face-content">
                  <div className="risk-ring-container">
                    <svg className="risk-ring-svg" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="42" className="ring-bg" />
                      <circle cx="50" cy="50" r="42" className={`ring-progress risk-ring-${risk}`} />
                    </svg>
                    <div className="risk-ring-text">
                      <span className="risk-label">OCEAN RISK</span>
                      <strong className={`risk-value risk-text-${risk}`}>{risk.toUpperCase()}</strong>
                    </div>
                  </div>

                  <div className="watch-complications-grid">
                    <div className="complication-card">
                      <span className="comp-label">WAVE</span>
                      <strong className="comp-value">{watchData?.ocean_summary.wave_height ?? "--"}</strong>
                    </div>
                    <div className="complication-card">
                      <span className="comp-label">TEMP</span>
                      <strong className="comp-value">{watchData?.ocean_summary.water_temp ?? "--"}</strong>
                    </div>
                    <div className="complication-card">
                      <span className="comp-label">WIND</span>
                      <strong className="comp-value">{watchData?.ocean_summary.wind_speed ?? "--"}</strong>
                    </div>
                    <div className="complication-card">
                      <span className="comp-label">PATROL</span>
                      <strong className="comp-value">78 BPM</strong>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "alert" && (
                <div className="watch-alert-content">
                  {alert ? (
                    <div className="watch-alert-banner">
                      <div className="alert-header">
                        <span className="alert-icon">⚠️</span>
                        <strong>HAZARD ALERT</strong>
                      </div>
                      <p className="alert-desc">{alert.description}</p>
                      <div className="watch-alert-actions">
                        <button
                          className="wrist-btn primary-wrist"
                          onClick={() => handleWristAction("acknowledge_alert", alert.id)}
                        >
                          ✓ ACKNOWLEDGE
                        </button>
                        <button
                          className="wrist-btn warning-wrist"
                          onClick={() => handleWristAction("trigger_whistle")}
                        >
                          ♪ WHISTLE
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="watch-clear-banner">
                      <span className="clear-icon">🛡️</span>
                      <strong>CLEAR SECTOR</strong>
                      <p>No active unacknowledged wrist hazards</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === "actions" && (
                <div className="watch-actions-content">
                  <span className="actions-title">QUICK WRIST CONTROLS</span>
                  <div className="wrist-actions-grid">
                    <button
                      className="wrist-action-tile"
                      onClick={() => handleWristAction("trigger_whistle")}
                    >
                      <span>🔊</span>
                      <small>Whistle</small>
                    </button>
                    <button
                      className="wrist-action-tile"
                      onClick={() => handleWristAction("dispatch_guard")}
                    >
                      <span>🛟</span>
                      <small>Backup</small>
                    </button>
                    <button
                      className="wrist-action-tile"
                      onClick={() => handleWristAction("ping_tower")}
                    >
                      <span>📡</span>
                      <small>Tower</small>
                    </button>
                    <button
                      className="wrist-action-tile danger"
                      onClick={() => handleWristAction("request_sos")}
                    >
                      <span>🚨</span>
                      <small>SOS 911</small>
                    </button>
                  </div>
                </div>
              )}

              {activeTab === "haptics" && (
                <div className="watch-haptics-content">
                  <span className="haptics-title">WRIST HAPTIC ENGINE</span>
                  <div className="haptic-info">
                    <strong>{watchData?.haptic_profile.label || "Normal Status Pulse"}</strong>
                    <p>{watchData?.haptic_profile.description || "Pattern ready"}</p>
                    <code className="pattern-code">
                      [{watchData?.haptic_profile.pattern.join(", ")} ms]
                    </code>
                  </div>
                  <button
                    className="vibrate-test-btn"
                    onClick={() =>
                      triggerHapticVibration(watchData?.haptic_profile.pattern || [300, 100, 300])
                    }
                  >
                    📳 TEST VIBRATION
                  </button>
                </div>
              )}

              {actionFeedback && <div className="watch-toast">{actionFeedback}</div>}
            </div>
          </div>

          <div className="watch-strap-bottom"></div>
        </div>

        {/* WATCH FEATURE EXPLANATION CARD */}
        <div className="watch-feature-info">
          <h4>Lifeguard Smartwatch Integration Features</h4>
          <ul>
            <li>
              <strong>Sunlight-optimized HUD:</strong> High-contrast OLED watch layout designed for direct outdoor ocean sunlight readability.
            </li>
            <li>
              <strong>Taptic Vibration Patterns:</strong> Custom haptic rhythms distinguish low monitoring ticks from urgent swimmer distress double-pulses.
            </li>
            <li>
              <strong>Wrist One-Tap Actions:</strong> Trigger public warning whistles, acknowledge AI hazards, or dispatch backup guards directly from the wrist without leaving the beach line.
            </li>
            <li>
              <strong>Real-Time Synchronization:</strong> Bidirectional state sync between smartwatch, Gemma multimodal vision/audio analysis, and main tower dashboard.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
