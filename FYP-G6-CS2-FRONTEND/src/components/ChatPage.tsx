import type { ChatMessage, ChatSession, SupportResource } from "../types";
import { useState } from "react";

interface ChatPageProps {
  sessions: ChatSession[];
  sessionId: string;
  messages: ChatMessage[];
  draft: string;
  busy: boolean;
  creatingSession: boolean;
  dataConsent: boolean;
  error: string;
  city: string;
  country: string;
  locationConsent: boolean;
  resources: SupportResource[];
  onCreateSession: () => void;
  onDataConsent: (granted: boolean) => void;
  onSelectSession: (id: string) => void;
  onCloseSession: (id: string) => void;
  onDraftChange: (draft: string) => void;
  onSend: () => void;
  onCityChange: (city: string) => void;
  onCountryChange: (country: string) => void;
  onLocationConsent: (granted: boolean) => void;
  onOfferChoice: (choice: "helpline" | "nearby_services" | "decline") => void;
  onFeedback: (id: string, helpful: boolean) => Promise<boolean>;
  onDismissError: () => void;
}

export function ChatPage(props: ChatPageProps) {
  const [feedback, setFeedback] = useState<Record<string, "saving" | "helpful" | "not_helpful">>({});
  async function submitFeedback(id: string, helpful: boolean) {
    setFeedback((current) => ({ ...current, [id]: "saving" }));
    const saved = await props.onFeedback(id, helpful);
    setFeedback((current) => {
      if (saved) return { ...current, [id]: helpful ? "helpful" : "not_helpful" };
      const next = { ...current };
      delete next[id];
      return next;
    });
  }
  return (
    <div className="workspace">
      <aside>
        <button className="primary full" disabled={props.creatingSession} onClick={props.onCreateSession}>
          {props.creatingSession ? "Starting…" : "＋ New conversation"}
        </button>
        <div className="sideLabel">RECENT CONVERSATIONS</div>
        {props.sessions.map((session) => (
          <div className="session-wrap" key={session.id}>
            <button
              className={`session ${props.sessionId === session.id ? "selected" : ""}`}
              onClick={() => props.onSelectSession(session.id)}
            >
              {session.title || sessionLabel(session.started_at)}
              <small>{new Date(session.started_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })} · {new Date(session.started_at).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}</small>
            </button>
            <button
              className="close-session"
              onClick={() => props.onCloseSession(session.id)}
              aria-label="Close session"
            >
              ×
            </button>
          </div>
        ))}
      </aside>

      <main className="chat">
        <div className="chatHead">
          <div>
            <div className="eyebrow">YOUR PRIVATE SPACE</div>
            <h2>Talk with Alex</h2>
          </div>
          <span className="online">● Here with you</span>
        </div>

        {!props.dataConsent && <div className="data-consent-banner"><div><b>Choose whether to save this conversation</b><p>Messages are encrypted at rest and saved to your account so you can return to them. You can change this choice in Settings.</p></div><label><input type="checkbox" onChange={(event) => props.onDataConsent(event.target.checked)} /> I agree to save my messages</label></div>}

        <div className="transcript">
          {!props.sessionId && (
            <div className="empty"><div className="sun">✳</div><h3>Your space is ready.</h3><p>Choose “New conversation” to begin. Your saved conversations will appear on the left.</p></div>
          )}
          {props.sessionId && !props.messages.length && (
            <div className="empty">
              <div className="sun">✳</div>
              <h3>Take your time.</h3>
              <p>There’s no right way to start. What’s been on your mind?</p>
            </div>
          )}
          {props.messages.map((message) => (
            <div className={`row ${message.role}`} key={message.id}>
              <div className="bubble">
                {message.content}
                {message.escalation_offer && (
                  <div className="escalate">
                    <p>{message.escalation_offer.text || "Would you like to explore a support option?"}</p>
                    <label className="consent">
                      <input
                        type="checkbox"
                        checked={props.locationConsent}
                        onChange={(event) => props.onLocationConsent(event.target.checked)}
                      />
                      I agree to a location lookup for the place I enter below.
                    </label>
                    <div className="loc">
                      <input
                        placeholder="City"
                        value={props.city}
                        onChange={(event) => props.onCityChange(event.target.value)}
                      />
                      <input
                        placeholder="Country"
                        value={props.country}
                        onChange={(event) => props.onCountryChange(event.target.value)}
                      />
                    </div>
                    <button onClick={() => props.onOfferChoice("helpline")}>Show helplines</button>
                    <button onClick={() => props.onOfferChoice("nearby_services")}>
                      Find nearby support
                    </button>
                    <button onClick={() => props.onOfferChoice("decline")}>No thanks</button>
                  </div>
                )}
              </div>
              {message.role === "assistant" && (
                <div className="feedback">
                  {feedback[message.id] ? <span className="feedback-thanks">{feedback[message.id] === "saving" ? "Saving…" : "Thanks for your feedback"}</span> : <>
                    <button disabled={feedback[message.id] === "saving"} onClick={() => void submitFeedback(message.id, true)}>♡ Helpful</button>
                    <button disabled={feedback[message.id] === "saving"} onClick={() => void submitFeedback(message.id, false)}>Not quite</button>
                  </>}
                </div>
              )}
            </div>
          ))}
          {props.busy && (
            <div className="typing">
              <i /> <i /> <i /> Thinking with care…
            </div>
          )}
          {props.resources.map((resource, index) => (
            <ResourceCard resource={resource} key={`${resource.source_url}-${index}`} />
          ))}
        </div>

        {props.error && (
          <div className="errorbar">
            {props.error}
            <button onClick={props.onDismissError}>Dismiss</button>
          </div>
        )}
        <div className="composer">
          <textarea
            value={props.draft}
            onChange={(event) => props.onDraftChange(event.target.value)}
            disabled={!props.dataConsent || !props.sessionId || props.busy}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                props.onSend();
              }
            }}
            placeholder={!props.dataConsent ? "Agree to message saving above to start chatting" : !props.sessionId ? "Start a new conversation to begin" : "Write what’s on your mind…"}
          />
          <button className="send" onClick={props.onSend} disabled={props.busy || !props.sessionId || !props.dataConsent || !props.draft.trim()} aria-label="Send message">
            ↑
          </button>
          <small>Your messages are encrypted at rest · Press Enter to send</small>
        </div>
      </main>
    </div>
  );
}

function sessionLabel(startedAt: string) {
  const date = new Date(startedAt);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  const sameDay = (a: Date, b: Date) => a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  const day = sameDay(date, today) ? "Today" : sameDay(date, yesterday) ? "Yesterday" : date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  return `Conversation · ${day} · ${date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}`;
}

function ResourceCard({ resource }: { resource: SupportResource }) {
  return (
    <div className="resource">
      <b>{resource.name}</b>
      {resource.phone && <a href={`tel:${resource.phone}`}>{resource.phone}</a>}
      {resource.hours && <small>{resource.hours}</small>}
      <a href={resource.source_url} target="_blank" rel="noreferrer">
        View source ↗
      </a>
      {resource.please_verify && <small>{resource.please_verify}</small>}
    </div>
  );
}
