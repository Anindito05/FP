interface WelcomePageProps {
  accepted: boolean;
  onAcceptedChange: (value: boolean) => void;
  onContinue: () => void;
}

export function WelcomePage({ accepted, onAcceptedChange, onContinue }: WelcomePageProps) {
  return (
    <main className="welcome">
      <div className="eyebrow">A SUPPORTIVE SPACE</div>
      <h1>
        Some days are
        <br />
        <em>heavier than others.</em>
      </h1>
      <p>Share what’s on your mind and find a little support, at your own pace.</p>
      <div className="notice">
        <b>A note before we begin</b>
        <p>
          Alex is an AI companion, not therapy or a crisis line. Alex does not diagnose or replace
          professional care.
        </p>
        <label>
          <input
            type="checkbox"
            checked={accepted}
            onChange={(event) => onAcceptedChange(event.target.checked)}
          />
          I understand and agree to the terms
        </label>
      </div>
      <button className="primary" onClick={onContinue} disabled={!accepted}>
        Continue <span>→</span>
      </button>
    </main>
  );
}
