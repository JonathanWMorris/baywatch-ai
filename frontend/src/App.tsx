import {useEffect, useMemo, useState} from "react";
import {AlertCard} from "./components/AlertCard";
import {CameraCard} from "./components/CameraCard";
import {Conditions} from "./components/Conditions";
import {Timeline} from "./components/Timeline";
import {API, acknowledgeAlert, analyzeMedia, getScenarios, getStatus, logAnnouncement, simulateEmergency, startScenario} from "./services/api";
import type {Camera, DashboardStatus, Scenario} from "./types";

const statusLabels: Record<string, string> = {monitoring: "Monitoring", elevated_conditions: "Elevated conditions", active_alert: "Active alert"};

function App() {
  const [status, setStatus] = useState<DashboardStatus>();
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [error, setError] = useState<string>();
  const [emergencyCamera, setEmergencyCamera] = useState<string>();
  const [speaking, setSpeaking] = useState(false);

  const refresh = async () => { try { setStatus(await getStatus()); setError(undefined); } catch (caught) { setError(caught instanceof Error ? caught.message : "Backend unavailable"); } };
  useEffect(() => { refresh(); getScenarios().then(setScenarios).catch(() => undefined); const timer=setInterval(refresh,5000); return () => clearInterval(timer); }, []);

  const activeAlert = useMemo(() => status?.alerts.find(alert => !alert.acknowledged), [status]);
  const suggestedWarning = status?.warning?.message || status?.assessments[activeAlert?.camera_id ?? ""]?.public_warning;

  async function analyze(camera: Camera, video?: File, audio?: File) {
    setError(undefined);
    try { await analyzeMedia(camera.id, video, audio); await refresh(); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Analysis failed"); }
  }

  async function runScenario(scenario: Scenario) {
    try {
      const started = await startScenario(scenario.id);
      if (!started.media_url) return;
      const blob = await fetch(`${API}${started.media_url}`).then(response => response.blob());
      await analyzeMedia(started.camera_id, new File([blob], started.media_file, {type: blob.type || "video/mp4"}));
      await refresh();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Scenario failed"); }
  }

  function whistle(): Promise<void> {
    return new Promise(resolve => {
      const AudioContextCtor = window.AudioContext || (window as typeof window & {webkitAudioContext: typeof AudioContext}).webkitAudioContext;
      const context = new AudioContextCtor(); const oscillator=context.createOscillator(); const gain=context.createGain();
      oscillator.type="square"; oscillator.frequency.setValueAtTime(2400,context.currentTime); gain.gain.setValueAtTime(.0001,context.currentTime); gain.gain.exponentialRampToValueAtTime(.14,context.currentTime+.03); gain.gain.exponentialRampToValueAtTime(.0001,context.currentTime+.65);
      oscillator.connect(gain).connect(context.destination); oscillator.start(); oscillator.stop(context.currentTime+.7); setTimeout(resolve,1000);
    });
  }

  async function announce(message?: string, cameraId?: string) {
    if (!message || speaking) return;
    setSpeaking(true); await whistle();
    const utterance = new SpeechSynthesisUtterance(message); utterance.rate=.92; utterance.pitch=.92;
    utterance.onend=() => setSpeaking(false); utterance.onerror=() => setSpeaking(false); speechSynthesis.cancel(); speechSynthesis.speak(utterance);
    await logAnnouncement(message,cameraId); await refresh();
  }

  if (!status) return <main className="loading-screen"><div className="brand-mark">B</div><h1>Baywatch AI</h1><p>{error ?? "Connecting to lifeguard command…"}</p></main>;
  const highestRisk = Object.values(status.assessments).sort((a,b) => ["unknown","low","moderate","high","critical"].indexOf(b.risk_level)-["unknown","low","moderate","high","critical"].indexOf(a.risk_level))[0];

  return <div className="app-shell">
    <header><div className="brand"><div className="brand-mark">B</div><div><h1>Baywatch AI</h1><p>Gemma-powered lifeguard support</p></div></div><div className="header-right"><span className={`model-chip ${status.gemma.loaded ? "ready" : ""}`}>Gemma {status.gemma.loaded ? `ready · ${status.gemma.device}` : "loads on first analysis"}</span><span className={`global-status ${status.global_status}`}><i/>{statusLabels[status.global_status]}</span></div></header>
    <main>
      <section className="hero-row"><div><span className="eyebrow">Santa Cruz · Unified beach view</span><h2>Another set of <em>eyes and ears.</em></h2><p>Gemma combines local video, native audio, buoy readings, and weather to identify situations that may require lifeguard attention.</p></div><div className={`risk-orb ${highestRisk?.risk_level ?? "moderate"}`}><span>Ocean risk assessment</span><strong>{highestRisk?.risk_level ?? "moderate"}</strong><small>Decision support · not a safety guarantee</small></div></section>
      {error && <div className="error-banner">{error}<button onClick={()=>setError(undefined)}>×</button></div>}
      <section className="scenario-bar"><div><span className="eyebrow">Reliable judge demo</span><strong>Scenario mode</strong></div><div className="scenario-buttons">{scenarios.map(item => <button className="scenario-button" disabled={!item.available} title={item.available ? item.expected_theme : `Add ${item.media_file} to demo_assets`} onClick={()=>runScenario(item)} key={item.id}>{item.name}{!item.available && <small>add clip</small>}</button>)}</div></section>
      <section className="camera-grid">{status.cameras.map(camera => <CameraCard key={camera.id} camera={camera} assessment={status.assessments[camera.id]} onAnalyze={analyze} apiBase={API}/>)}</section>
      <section className="dashboard-grid"><div><Conditions ocean={status.ocean} weather={status.weather}/>{activeAlert ? <AlertCard alert={activeAlert} onAcknowledge={async()=>{await acknowledgeAlert(activeAlert.id); await refresh();}} onWarning={()=>announce(suggestedWarning ?? activeAlert.description,activeAlert.camera_id)} onEscalate={()=>setEmergencyCamera(activeAlert.camera_id)}/> : <section className="clear-state"><span>✓</span><div><h2>No active lifeguard alerts</h2><p>Monitoring continues across all camera and audio feeds.</p></div></section>}{suggestedWarning && <section className="warning-preview"><span className="eyebrow">Gemma-prepared public warning</span><p>“{suggestedWarning}”</p><button onClick={()=>announce(suggestedWarning,status.warning?.camera_id)} disabled={speaking}>{speaking ? "Announcing…" : "♪ Whistle + announce"}</button></section>}</div><Timeline events={status.events}/></section>
      <section className="safety-note"><strong>Human in the loop</strong><p>Baywatch AI augments trained lifeguards. It does not diagnose drowning, determine whether someone is unresponsive, guarantee water safety, or automatically contact emergency services.</p></section>
    </main>
    {emergencyCamera && <div className="modal-backdrop"><div className="modal"><div className="alert-icon">!</div><span className="eyebrow">Human confirmation required</span><h2>Emergency escalation recommended</h2><p>Gemma recommends immediate lifeguard review near {emergencyCamera.replace("_"," ")}. This hackathon control never contacts real emergency services.</p><button className="danger-button" onClick={async()=>{await simulateEmergency(emergencyCamera);setEmergencyCamera(undefined);await refresh();}}>Simulate call 911</button><button className="secondary" onClick={()=>setEmergencyCamera(undefined)}>Dismiss</button></div></div>}
  </div>;
}

export default App;

