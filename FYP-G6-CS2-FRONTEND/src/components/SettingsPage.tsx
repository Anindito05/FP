import type { ConsentType } from "../types";

interface SettingsPageProps {
  onConsentChange: (type: ConsentType, granted: boolean) => Promise<void>;
  onBack: () => void;
  onDeleteAccount: () => Promise<void>;
  consents: Record<ConsentType, boolean>;
}

const preferences: Array<{ type: ConsentType; description: string }> = [
  { type: "data_logging", description: "Save encrypted messages to your account." },
  { type: "location_lookup", description: "Search support options using a location you provide." },
  { type: "research_use", description: "Use de-identified records for research." },
];

export function SettingsPage({ onConsentChange, onBack, onDeleteAccount, consents }: SettingsPageProps) {
  return (
    <main className="card settings">
      <div className="eyebrow">YOUR CHOICES</div>
      <h2>Consent settings</h2>
      <p>You can change these preferences at any time.</p>
      {preferences.map(({ type, description }) => (
        <label className="pref" key={type}>
          <span>
            <b>{type.replace(/_/g, " ")}</b>
            <small>{description}</small>
          </span>
          <input
            type="checkbox"
            checked={consents[type]}
            onChange={(event) => void onConsentChange(type, event.target.checked)}
          />
        </label>
      ))}
      <button className="link" onClick={onBack}>
        ← Back to conversation
      </button>
      <div className="danger">
        <b>Account</b>
        <p>You can log out or request account deletion.</p>
        <button
          onClick={() => {
            if (confirm("Delete your account and saved data?")) void onDeleteAccount();
          }}
        >
          Delete account
        </button>
      </div>
    </main>
  );
}
