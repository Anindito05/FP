import { useEffect, useState } from "react";
import { api } from "../api/client";
import type {
  AdminData,
  AuthKind,
  ChatMessage,
  ChatSession,
  ConsentType,
  Page,
  SupportResource,
  User,
} from "../types";

function messageOf(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

export function useAppController() {
  const [access, setAccess] = useState("");
  const [page, setPage] = useState<Page>(
    localStorage.getItem("accepted") ? "auth" : "welcome",
  );
  const [user, setUser] = useState<User | null>(null);
  const [terms, setTerms] = useState(false);
  const [authTerms, setAuthTerms] = useState(false);
  const [authBusy, setAuthBusy] = useState(false);
  const [dataConsent, setDataConsent] = useState(false);
  const [creatingSession, setCreatingSession] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [city, setCity] = useState("");
  const [country, setCountry] = useState("");
  const [locationConsent, setLocationConsent] = useState(false);
  const [researchConsent, setResearchConsent] = useState(false);
  const [resources, setResources] = useState<SupportResource[]>([]);
  const [adminData, setAdminData] = useState<AdminData>({ events: [], metrics: null });

  useEffect(() => {
    api.subscribeToTokenChange(setAccess);
    void (async () => {
      const tokens = await api.restoreSession();
      if (!tokens) return;
      try {
        const currentUser = await api.request<User>("/users/me");
        setUser(currentUser);
        setPage("chat");
      } catch {
        api.clearSession();
        setPage("auth");
      }
    })();
  }, []);

  useEffect(() => {
    if (!access) return;
    let active = true;
    void Promise.all([
      api.request<ChatSession[]>("/sessions"),
      api.request<Array<{ type: string; granted: boolean }>>("/consents"),
    ]).then(([items, consents]) => {
      if (!active) return;
      setSessions(items);
      setDataConsent(consents.some((item) => item.type === "data_logging" && item.granted));
      setLocationConsent(consents.some((item) => item.type === "location_lookup" && item.granted));
      setResearchConsent(consents.some((item) => item.type === "research_use" && item.granted));
    }).catch((cause: unknown) => { if (active) setError(messageOf(cause)); });
    return () => {
      active = false;
    };
  }, [access]);

  async function loadSessions() {
    try {
      setSessions(await api.request<ChatSession[]>("/sessions"));
    } catch (cause) {
      setError(messageOf(cause));
    }
  }

  function acceptDisclaimer() {
    if (!terms) return;
    localStorage.setItem("accepted", "1");
    setPage("auth");
  }

  async function authenticate(kind: AuthKind) {
    setError("");
    if (kind !== "guest" && !authTerms) { setError("Please agree to the Terms & Conditions before continuing."); return; }
    if (kind === "register" && password.length < 10) { setError("Your password must be at least 10 characters."); return; }
    if (kind !== "guest" && (!email.trim() || !password)) { setError("Enter your email and password to continue."); return; }
    setAuthBusy(true);
    const body =
      kind === "guest"
        ? { accepted_terms: true }
        : {
            email,
            password,
            ...(kind === "register" ? { display_name: name, accepted_terms: authTerms } : {}),
          };
    try {
      const tokens = await api.request<{ access_token: string; refresh_token: string }>(
        `/auth/${kind}`,
        { method: "POST", body, authenticated: false },
      );
      sessionStorage.setItem("refresh", tokens.refresh_token);
      api.setAccessToken(tokens.access_token);
      setUser(await api.request<User>("/users/me"));
      setPage("chat");
      setAuthTerms(false);
      await loadSessions();
    } catch (cause) {
      const error = cause as Error & { status?: number };
      if (kind === "register" && error.status === 409) {
        setError("An account with this email already exists. Log in with your password, or use a different email to register.");
      } else if (kind === "login" && error.status === 401) {
        setError("We couldn’t sign you in with that email and password. Check them and try again.");
      } else setError(messageOf(cause));
    } finally {
      setAuthBusy(false);
    }
  }

  async function logout() {
    try {
      await api.request("/auth/logout", {
        method: "POST",
        body: { refresh_token: sessionStorage.getItem("refresh") },
      });
    } catch {
      // Clear local credentials even when the API is unavailable.
    }
    api.clearSession();
    setUser(null);
    setPage("auth");
  }

  async function createSession() {
    setCreatingSession(true);
    try {
      const created = await api.request<ChatSession>("/sessions", {
        method: "POST",
        body: { mode: "text" },
      });
      setSessionId(created.id);
      setMessages([]);
      setResources([]);
      await loadSessions();
    } catch (cause) {
      setError(messageOf(cause));
    } finally {
      setCreatingSession(false);
    }
  }

  async function selectSession(id: string) {
    try {
      setSessionId(id); setMessages([]); setError("");
      setResources([]);
      setMessages(await api.request<ChatMessage[]>(`/sessions/${id}/messages`));
    } catch (cause) {
      setError(messageOf(cause));
    }
  }

  async function closeSession(id: string) {
    try {
      await api.request(`/sessions/${id}/close`, { method: "POST", body: {} });
      setSessions((existing) => existing.filter((item) => item.id !== id));
      if (sessionId === id) {
        setSessionId("");
        setMessages([]);
      }
    } catch (cause) {
      setError(messageOf(cause));
    }
  }

  async function sendMessage() {
    if (!draft.trim() || busy || !sessionId) return;
    const content = draft.trim();
    const clientMessageId = crypto.randomUUID();
    setDraft("");
    setBusy(true);
    setError("");
    setMessages((existing) => [
      ...existing,
      { id: clientMessageId, role: "user", content, route: "normal" },
    ]);
    try {
      const response = await api.request<ChatMessage>(`/chat/${sessionId}/messages`, {
        method: "POST",
        body: { content, client_msg_id: clientMessageId },
      });
      setMessages((existing) => [...existing, response]);
    } catch (cause) {
      setError(messageOf(cause));
      setDraft(content);
    } finally {
      setBusy(false);
    }
  }

  async function respondToOffer(choice: "helpline" | "nearby_services" | "decline") {
    if (choice !== "decline" && !locationConsent) {
      setError("Please accept location lookup consent first.");
      return;
    }
    try {
      const latestOffer = [...messages].reverse().find((item) => item.escalation_offer);
      const response = await api.request<ChatMessage>(`/chat/${sessionId}/escalation`, {
        method: "POST",
        body: {
          offer_id: latestOffer?.escalation_offer?.offer_id,
          choice,
          country,
          city,
        },
      });
      setMessages((existing) => [...existing, response]);
      if (choice !== "decline") {
        const endpoint = choice === "helpline" ? "helplines" : "nearby";
        const query = new URLSearchParams({ country, city });
        setResources(
          await api.request<SupportResource[]>(`/resources/${endpoint}?${query.toString()}`),
        );
      }
    } catch (cause) {
      setError(messageOf(cause));
    }
  }

  async function updateConsent(type: ConsentType, granted: boolean) {
    const previous = type === "data_logging" ? dataConsent : type === "location_lookup" ? locationConsent : researchConsent;
    if (type === "data_logging") setDataConsent(granted);
    if (type === "location_lookup") setLocationConsent(granted);
    if (type === "research_use") setResearchConsent(granted);
    try {
      await api.request("/consents", {
        method: "PUT",
        body: { type, granted, version: "v1" },
      });
      if (type === "location_lookup") setLocationConsent(granted);
    } catch (cause) {
      if (type === "data_logging") setDataConsent(previous);
      if (type === "location_lookup") setLocationConsent(previous);
      if (type === "research_use") setResearchConsent(previous);
      setError(messageOf(cause));
    }
  }

  async function submitFeedback(messageId: string, helpful: boolean) {
    try {
      await api.request("/feedback", {
        method: "POST",
        body: { message_id: messageId, rating: helpful ? 5 : 1, helpful },
      });
      return true;
    } catch (cause) {
      setError(messageOf(cause));
      return false;
    }
  }

  async function openAdmin() {
    try {
      const [events, metrics, mood] = await Promise.all([
        api.request<AdminData["events"]>("/admin/risk-events"),
        api.request<NonNullable<AdminData["metrics"]>>("/admin/metrics"),
        sessionId ? api.request<NonNullable<AdminData["mood"]>>(`/admin/sessions/${sessionId}/mood`) : Promise.resolve([]),
      ]);
      setAdminData({ events, metrics, mood });
      setPage("admin");
    } catch (cause) {
      setError(messageOf(cause));
    }
  }

  async function reviewRiskEvent(eventId: string) {
    try {
      await api.request(`/admin/risk-events/${eventId}/review`, {
        method: "POST",
        body: { review_label: "true_positive" },
      });
      await openAdmin();
    } catch (cause) {
      setError(messageOf(cause));
    }
  }

  async function deleteAccount() {
    try {
      await api.request("/users/me", { method: "DELETE" });
      api.clearSession();
      setUser(null);
      setPage("auth");
    } catch (cause) {
      setError(messageOf(cause));
    }
  }

  return {
    access,
    user,
    page,
    setPage,
    terms,
    setTerms,
    authTerms,
    setAuthTerms,
    authBusy,
    dataConsent,
    creatingSession,
    email,
    setEmail,
    password,
    setPassword,
    name,
    setName,
    sessions,
    sessionId,
    messages,
    draft,
    setDraft,
    busy,
    error,
    setError,
    city,
    setCity,
    country,
    setCountry,
    locationConsent,
    researchConsent,
    resources,
    adminData,
    acceptDisclaimer,
    authenticate,
    logout,
    createSession,
    selectSession,
    closeSession,
    sendMessage,
    respondToOffer,
    updateConsent,
    submitFeedback,
    openAdmin,
    reviewRiskEvent,
    deleteAccount,
  };
}
