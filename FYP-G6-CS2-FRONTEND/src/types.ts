export type Page = "welcome" | "auth" | "chat" | "settings" | "admin";
export type AuthKind = "login" | "register" | "guest";

export interface User {
  id: string;
  role: string;
  email: string | null;
}

export interface ChatSession {
  id: string;
  title: string | null;
  status: string;
  started_at: string;
  message_count: number;
}

export interface EscalationOffer {
  offer_id: string;
  text: string;
  options: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  route: string;
  escalation_offer?: EscalationOffer;
  level?: number;
  trend?: string;
  shift_flag?: string | null;
  classifier_mode?: string;
}

export interface SupportResource {
  name: string;
  phone?: string | null;
  hours?: string | null;
  url?: string | null;
  source_url: string;
  languages?: string[];
  please_verify?: string;
}

export interface AdminData {
  events: Array<{
    id: string;
    risk_level: string;
    created_at: string;
    action_taken: string;
  }>;
  metrics: {
    avg_latency_ms?: number | null;
    escalation_rate?: number | null;
  } | null;
  mood?: Array<{turn_index:number;level:number;instant_level:number;emotion_top:string;trend:string;shift_flag:string|null;index_version:string|null}>;
}

export type ConsentType = "data_logging" | "location_lookup" | "research_use";
