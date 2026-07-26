import type {Alert} from "../types";

export function AlertCard({alert, onAcknowledge, onWarning, onEscalate}: {alert: Alert; onAcknowledge: () => void; onWarning: () => void; onEscalate: () => void}) {
  return <section className={`alert-card ${alert.severity}`}>
    <div className="alert-title"><span className="alert-icon">!</span><div><span className="eyebrow">Lifeguard attention recommended</span><h2>{alert.type.replaceAll("_", " ")}</h2><p>{alert.camera_id.replace("_", " ")}</p></div><strong>{Math.round(alert.confidence * 100)}%</strong></div>
    <p>{alert.description}</p>
    {alert.evidence.length > 0 && <ul>{alert.evidence.map(item => <li key={item}>{item}</li>)}</ul>}
    <div className="alert-actions"><button onClick={onAcknowledge}>Acknowledge</button><button className="warning-button" onClick={onWarning}>Whistle + announce</button><button className="danger-button" onClick={onEscalate}>Emergency escalation</button></div>
  </section>;
}

