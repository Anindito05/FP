import type { AdminData } from "../types";

interface AdminPageProps {
  data: AdminData;
  onReview: (eventId: string) => void;
  onBack: () => void;
}

export function AdminPage({ data, onReview, onBack }: AdminPageProps) {
  return (
    <main className="card settings">
      <div className="eyebrow">REVIEWER SPACE</div>
      <h2>Safety review</h2>
      <p>Risk events for authorized reviewers.</p>
      <div className="metrics">
        <b>Average response time</b>
        <span>{data.metrics?.avg_latency_ms?.toFixed?.(0) ?? "—"} ms</span>
        <b>Escalation rate</b>
        <span>{data.metrics?.escalation_rate?.toFixed?.(2) ?? "—"}</span>
      </div>
      <h3>Unreviewed events</h3>
      {data.events.map((event) => (
        <div className="pref" key={event.id}>
          <span>
            <b>{event.risk_level}</b>
            <small>
              {new Date(event.created_at).toLocaleString()} · {event.action_taken}
            </small>
          </span>
          <button onClick={() => onReview(event.id)}>Mark reviewed</button>
        </div>
      ))}
      {!data.events.length && <p>No events are waiting for review.</p>}
      <h3>Mood timeline (labels only)</h3>
      {(data.mood ?? []).map((turn) => <div className="pref" key={turn.turn_index}><span><b>Turn {turn.turn_index}: {turn.emotion_top}, level {turn.level}</b><small>{turn.trend}{turn.shift_flag ? ` · ${turn.shift_flag} shift` : ""} · index {turn.index_version ?? "none"}</small></span></div>)}
      <button className="link" onClick={onBack}>
        ← Back to chat
      </button>
    </main>
  );
}
