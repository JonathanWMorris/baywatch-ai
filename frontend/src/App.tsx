import {useEffect, useMemo, useState} from "react";
import {AlertCard} from "./components/AlertCard";
import {CameraCard} from "./components/CameraCard";
import {Conditions} from "./components/Conditions";
import {HandWearablePanel} from "./components/HandWearablePanel";
import {IoTPanel} from "./components/IoTPanel";
import {ProductionSuitePanel} from "./components/ProductionSuitePanel";
import {Timeline} from "./components/Timeline";
import {WatchSimulator} from "./components/WatchSimulator";
import {
  acknowledgeAlert,
  getStatus,
  logAnnouncement,
  simulateEmergency,
  startLiveAnalysis,
  stopLiveAnalysis,
} from "./services/api";
import type {DashboardStatus} from "./types";

const statusLabels: Record<string, string> = {
  monitoring: "Monitoring",
  elevated_conditions: "Elevated conditions",
  active_alert: "Active alert",
};

function App() {
  const [status, setStatus] = useState<DashboardStatus>();
  const [error, setError] = useState<string>();
  const [emergencyCamera, setEmergencyCamera] = useState<string>();
  const [speaking, setSpeaking] = useState(false);

  const refresh = async () => {
    try {
      setStatus(await getStatus());
      setError(undefined);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Backend unavailable");
    }
  };

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 5000);
    return () => clearInterval(timer);
  }, []);

  const activeAlert = useMemo(
    () => status?.alerts.find(alert => !alert.acknowledged),
    [status],
  );
  const suggestedWarning =
    status?.warning?.message ||
    status?.assessments[activeAlert?.camera_id ?? ""]?.public_warning;

  async function toggleLive(enabled: boolean) {
    setError(undefined);
    try {
      if (enabled) await startLiveAnalysis();
      else await stopLiveAnalysis();
      await refresh();
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Live analysis control failed",
      );
    }
  }

  function whistle(): Promise<void> {
    return new Promise(resolve => {
      const AudioContextCtor =
        window.AudioContext ||
        (window as typeof window & {webkitAudioContext: typeof AudioContext})
          .webkitAudioContext;
      const context = new AudioContextCtor();
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.type = "square";
      oscillator.frequency.setValueAtTime(2400, context.currentTime);
      gain.gain.setValueAtTime(0.0001, context.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.14, context.currentTime + 0.03);
      gain.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + 0.65);
      oscillator.connect(gain).connect(context.destination);
      oscillator.start();
      oscillator.stop(context.currentTime + 0.7);
      setTimeout(resolve, 1000);
    });
  }

  async function announce(message?: string, cameraId?: string) {
    if (!message || speaking) return;
    setSpeaking(true);
    await whistle();
    const utterance = new SpeechSynthesisUtterance(message);
    utterance.rate = 0.92;
    utterance.pitch = 0.92;
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    speechSynthesis.cancel();
    speechSynthesis.speak(utterance);
    await logAnnouncement(message, cameraId);
    await refresh();
  }

  if (!status) {
    return (
      <main className="loading-screen">
        <div className="brand-mark">B</div>
        <h1>Baywatch AI</h1>
        <p>{error ?? "Connecting to lifeguard command…"}</p>
      </main>
    );
  }

  const camera = status.cameras[0];
  const risk = status.ocean_risk_assessment;

  return (
    <div className="app-shell">
      <header>
        <div className="brand">
          <div className="brand-mark">B</div>
          <div>
            <h1>Baywatch AI</h1>
            <p>Gemma-powered lifeguard support</p>
          </div>
        </div>
        <div className="header-right">
          <span className={`model-chip ${status.gemma.loaded ? "ready" : ""}`}>
            Gemma{" "}
            {status.gemma.loaded
              ? `ready · ${status.gemma.device}`
              : "loads on first analysis"}
          </span>
          <span className={`global-status ${status.global_status}`}>
            <i />
            {statusLabels[status.global_status]}
          </span>
        </div>
      </header>

      <main>
        <section className="hero-row">
          <div>
            <span className="eyebrow">
              Deerfield Beach, Florida · Live waterfront
            </span>
            <h2>
              Another set of <em>eyes and ears.</em>
            </h2>
            <p>
              Gemma combines live beach video, native audio, nearby Atlantic
              buoy readings, and local weather to identify situations that may
              require lifeguard attention.
            </p>
          </div>
          <div className={`risk-orb ${risk.risk_level}`}>
            <span>Ocean risk assessment</span>
            <strong>{risk.risk_level}</strong>
            <small>
              {risk.source_mode === "demo" ? "Includes demo data" : "Live sources"}
              {" · "}not a safety guarantee
            </small>
          </div>
        </section>

        {error && (
          <div className="error-banner">
            {error}
            <button onClick={() => setError(undefined)}>×</button>
          </div>
        )}

        <section className="live-stage">
          <CameraCard
            camera={camera}
            assessment={status.assessments[camera.id]}
            live={status.live}
            onLiveToggle={toggleLive}
          />
          <aside className={`risk-summary risk-${risk.risk_level}`}>
            <span className="eyebrow">Why this level</span>
            <h2>Current risk factors</h2>
            <p>{risk.summary}</p>
            <ul>
              {risk.factors.map(factor => (
                <li key={factor}>{factor}</li>
              ))}
            </ul>
            <div className="source-list">
              {risk.sources.map(source => (
                <span key={source}>{source}</span>
              ))}
            </div>
          </aside>
        </section>

        <Conditions ocean={status.ocean} weather={status.weather} />

        <section className="dashboard-grid">
          <div>
            {activeAlert ? (
              <AlertCard
                alert={activeAlert}
                onAcknowledge={async () => {
                  await acknowledgeAlert(activeAlert.id);
                  await refresh();
                }}
                onWarning={() =>
                  announce(
                    suggestedWarning ?? activeAlert.description,
                    activeAlert.camera_id,
                  )
                }
                onEscalate={() => setEmergencyCamera(activeAlert.camera_id)}
              />
            ) : (
              <section className="clear-state">
                <span>✓</span>
                <div>
                  <h2>No active lifeguard alerts</h2>
                  <p>
                    Monitoring continues across the live video, audio, and
                    environmental sources.
                  </p>
                </div>
              </section>
            )}
            {suggestedWarning && (
              <section className="warning-preview">
                <span className="eyebrow">Gemma-prepared public warning</span>
                <p>“{suggestedWarning}”</p>
                <button
                  onClick={() =>
                    announce(suggestedWarning, status.warning?.camera_id)
                  }
                  disabled={speaking}
                >
                  {speaking ? "Announcing…" : "♪ Whistle + announce"}
                </button>
              </section>
            )}
          </div>
          <Timeline events={status.events} />
        </section>

        <HandWearablePanel onRefreshParent={refresh} />
        <IoTPanel onRefreshParent={refresh} />
        <WatchSimulator onRefreshParent={refresh} />
        <ProductionSuitePanel onRefreshParent={refresh} />

        <section className="safety-note">
          <strong>Human in the loop</strong>
          <p>
            Baywatch AI augments trained lifeguards. It does not diagnose
            drowning, determine whether someone is unresponsive, guarantee
            water safety, or automatically contact emergency services.
          </p>
        </section>
      </main>

      {emergencyCamera && (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="alert-icon">!</div>
            <span className="eyebrow">Human confirmation required</span>
            <h2>Emergency escalation recommended</h2>
            <p>
              Gemma recommends immediate lifeguard review. This hackathon
              control never contacts real emergency services.
            </p>
            <button
              className="danger-button"
              onClick={async () => {
                await simulateEmergency(emergencyCamera);
                setEmergencyCamera(undefined);
                await refresh();
              }}
            >
              Simulate call 911
            </button>
            <button
              className="secondary"
              onClick={() => setEmergencyCamera(undefined)}
            >
              Dismiss
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
