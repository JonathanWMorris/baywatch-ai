import {useRef, useState} from "react";
import type {Assessment, Camera} from "../types";

interface Props { camera: Camera; assessment?: Assessment; onAnalyze: (camera: Camera, video?: File, audio?: File) => Promise<void>; apiBase: string }

export function CameraCard({camera, assessment, onAnalyze, apiBase}: Props) {
  const [video, setVideo] = useState<File>();
  const [audio, setAudio] = useState<File>();
  const [preview, setPreview] = useState<string>();
  const [busy, setBusy] = useState(false);
  const picker = useRef<HTMLInputElement>(null);
  const submit = async () => { if (!video && !audio) return picker.current?.click(); setBusy(true); try { await onAnalyze(camera, video, audio); } finally { setBusy(false); } };
  const source = preview || (camera.media_url ? `${apiBase}${camera.media_url}` : undefined);
  const latest = assessment?.events?.[0] ?? assessment?.audio_observations?.[0];
  return <article className={`camera-card risk-${camera.risk_level}`}>
    <div className="camera-head"><div><span className="eyebrow">{camera.id.replace("_", " ")}</span><h3>{camera.name}</h3></div><span className={`risk-pill ${camera.risk_level}`}>{camera.risk_level}</span></div>
    <div className="video-shell">
      {source ? <video src={source} controls muted loop autoPlay playsInline /> : <div className="empty-feed"><span>◉</span><strong>Feed ready</strong><small>Add a prerecorded beach clip</small></div>}
      <span className="live-chip">● SIMULATED LIVE</span>
    </div>
    <p className="latest-event">{latest?.description ?? "No recent hazards detected"}</p>
    <div className="camera-actions">
      <input ref={picker} hidden type="file" accept="video/*" onChange={event => {const file=event.target.files?.[0]; setVideo(file); if(file) setPreview(URL.createObjectURL(file));}} />
      <label className="file-action">Audio<input hidden type="file" accept="audio/*" onChange={event => setAudio(event.target.files?.[0])}/></label>
      <button className="secondary" onClick={() => picker.current?.click()}>{video ? "Change clip" : "Add clip"}</button>
      <button onClick={submit} disabled={busy}>{busy ? "Gemma analyzing…" : "Analyze"}</button>
    </div>
  </article>;
}

