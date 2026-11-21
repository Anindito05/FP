import type { AuthKind } from "../types";
import { useState } from "react";

interface AuthPageProps {
  name: string;
  email: string;
  password: string;
  error: string;
  acceptedTerms: boolean;
  busy: boolean;
  onNameChange: (value: string) => void;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onAcceptedTermsChange: (value: boolean) => void;
  onClearError: () => void;
  onAuthenticate: (kind: AuthKind) => void;
}

export function AuthPage(props: AuthPageProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const submit = (kind: AuthKind) => (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    props.onAuthenticate(kind);
  };
  return (
    <main className="auth card">
      <div className="eyebrow">WELCOME</div>
      <h2>{mode === "login" ? "Welcome back." : "Create your account."}</h2>
      <p>{mode === "login" ? "Sign in to continue your support journey." : "A few details to create your private account."}</p>
      <div className="auth-tabs" role="tablist" aria-label="Account access">
        <button type="button" role="tab" aria-selected={mode === "login"} className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>Log in</button>
        <button type="button" role="tab" aria-selected={mode === "register"} className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>Create account</button>
      </div>
      {mode === "login" ? <form onSubmit={submit("login")}>
        <label className="field-label" htmlFor="auth-email">Email address</label>
        <input id="auth-email" type="email" autoComplete="email" placeholder="you@example.com" required value={props.email} onChange={(event) => props.onEmailChange(event.target.value)} />
        <label className="field-label" htmlFor="auth-password">Password</label>
        <input id="auth-password" type="password" autoComplete="current-password" placeholder="Enter your password" required value={props.password} onChange={(event) => props.onPasswordChange(event.target.value)} />
        <label className="terms-check"><input type="checkbox" required checked={props.acceptedTerms} onChange={(event) => props.onAcceptedTermsChange(event.target.checked)} /> I agree to the <a href="/terms" target="_blank" rel="noreferrer">Terms &amp; Conditions</a> and understand this is a support tool, not therapy or emergency care.</label>
        <button className="primary auth-submit" type="submit" disabled={props.busy}>{props.busy ? "Signing in…" : "Log in"}</button>
      </form> : <form onSubmit={submit("register")}>
          <label className="field-label" htmlFor="auth-name">Name</label>
          <input id="auth-name" autoComplete="name" placeholder="Your name" required minLength={1} maxLength={120} value={props.name} onChange={(event) => props.onNameChange(event.target.value)} />
          <label className="field-label" htmlFor="register-email">Email</label>
          <input id="register-email" type="email" autoComplete="email" placeholder="you@example.com" required value={props.email} onChange={(event) => props.onEmailChange(event.target.value)} />
          <label className="field-label" htmlFor="register-password">Create password</label>
          <input id="register-password" type="password" autoComplete="new-password" placeholder="At least 10 characters" required minLength={10} maxLength={256} value={props.password} onChange={(event) => props.onPasswordChange(event.target.value)} />
          <small className="field-hint">Use at least 10 characters. This helps protect your account.</small>
          <label className="terms-check"><input type="checkbox" required checked={props.acceptedTerms} onChange={(event) => props.onAcceptedTermsChange(event.target.checked)} /> I have read and agree to the <a href="/terms" target="_blank" rel="noreferrer">Terms &amp; Conditions</a> and understand this is a support tool, not therapy or emergency care.</label>
          <button className="primary auth-submit" type="submit" disabled={props.busy || !props.acceptedTerms}>{props.busy ? "Creating…" : "Agree & create account"}</button>
        </form>}
      <div className="auth-divider"><span>or</span></div>
      <button className="guest-button" disabled={props.busy} onClick={() => props.onAuthenticate("guest")}>Continue as guest</button>
      {props.error && <div className="auth-error" role="alert"><span>{props.error}</span>{props.error.toLowerCase().includes("already exists") && <button type="button" onClick={() => { setMode("login"); props.onClearError(); }}>Go to log in</button>}</div>}
    </main>
  );
}
