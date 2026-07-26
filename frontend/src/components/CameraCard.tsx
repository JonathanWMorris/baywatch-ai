import type {Assessment, Camera, LiveStatus} from "../types";

interface Props {
  camera: Camera;
  assessment?: Assessment;
  live: LiveStatus;
  onLiveToggle: (enabled: boolean) => Promise<void>;
}

export function CameraCard({
  camera,
  assessment,
  live,
  onLiveToggle,
}: Props) {
  const latest =
    assessment?.events?.[0] ?? assessment?.audio_observations?.[0];
  const nextRun = live.next_analysis_at
    ? Math.max(
        0,
        Math.ceil(
          (new Date(live.next_analysis_at).getTime() - Date.now()) / 1000,
        ),
      )
    : null;

  return (
    <article className={`camera-card live-camera risk-${camera.risk_level}`}>
      <div className="camera-head">
        <div>
          <span className="eyebrow">YouTube live · Deerfield Beach Pier</span>
          <h3>{camera.name}</h3>
        </div>
        <span className={`risk-pill ${camera.risk_level}`}>
          {camera.risk_level} risk
        </span>
      </div>
      <div className="video-shell">
        <iframe
          src={camera.embed_url}
          title={camera.name}
          allow="autoplay; encrypted-media; picture-in-picture"
          allowFullScreen
        />
        <span className="live-chip">● LIVE</span>
      </div>
      <div className="camera-foot">
        <div>
          <p className="latest-event">
            {latest?.description ??
              "Awaiting the next Gemma video and audio assessment"}
          </p>
          <div className="live-meta">
            <span className={`live-state ${live.phase}`}>
              {live.phase.replace("_", " ")}
            </span>
            <span>Video + native audio + environment</span>
            {nextRun !== null && <span>Next window in {nextRun}s</span>}
          </div>
          {live.error && <p className="camera-error">{live.error}</p>}
        </div>
        <div className="camera-actions">
          <button
            className={live.enabled ? "danger-button" : ""}
            onClick={() => onLiveToggle(!live.enabled)}
          >
            {live.enabled ? "Stop analysis" : "Start live analysis"}
          </button>
          <a
            className="external-link"
            href={live.watch_url}
            target="_blank"
            rel="noreferrer"
          >
            Open YouTube ↗
          </a>
        </div>
      </div>
    </article>
  );
}
