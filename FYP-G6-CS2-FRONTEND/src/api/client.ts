const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  authenticated?: boolean;
  token?: string;
  retriedAfterRefresh?: boolean;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

class ApiClient {
  private accessToken = "";
  private onTokenChange?: (token: string) => void;
  private restorePending: Promise<{ access_token: string; refresh_token: string } | null> | null = null;

  setAccessToken(token: string) {
    this.accessToken = token;
    this.onTokenChange?.(token);
  }

  subscribeToTokenChange(callback: (token: string) => void) {
    this.onTokenChange = callback;
  }

  restoreSession() {
    if (this.restorePending) return this.restorePending;
    const refreshToken = sessionStorage.getItem("refresh");
    if (!refreshToken) return Promise.resolve(null);
    this.restorePending = this.refresh(refreshToken)
      .catch(() => {
        sessionStorage.removeItem("refresh");
        this.accessToken = "";
        this.onTokenChange?.("");
        return null;
      })
      .finally(() => {
        this.restorePending = null;
      });
    return this.restorePending;
  }

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const response = await this.fetch(path, options);
    if (
      response.status === 401 &&
      options.authenticated !== false &&
      !options.retriedAfterRefresh
    ) {
      const refreshed = await this.restoreSession();
      if (refreshed) {
        return this.request<T>(path, {
          ...options,
          token: refreshed.access_token,
          retriedAfterRefresh: true,
        });
      }
    }
    if (!response.ok) {
      const message = await this.errorMessage(response);
      throw new ApiError(message, response.status);
    }
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }

  forgetExpiredSession() {
    this.clearSession();
  }

  async refresh(refreshToken: string) {
    const response = await this.fetch("/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken },
      authenticated: false,
    });
    if (!response.ok) throw new ApiError("Session expired. Please sign in again.", response.status);
    const tokens = (await response.json()) as {
      access_token: string;
      refresh_token: string;
    };
    sessionStorage.setItem("refresh", tokens.refresh_token);
    this.setAccessToken(tokens.access_token);
    return tokens;
  }

  clearSession() {
    this.accessToken = "";
    sessionStorage.removeItem("refresh");
    this.onTokenChange?.("");
  }

  private fetch(path: string, options: RequestOptions) {
    const method = options.method ?? (options.body === undefined ? "GET" : "POST");
    const token = options.token ?? this.accessToken;
    return fetch(API_BASE + path, {
      method,
      headers: {
        ...(options.body === undefined ? {} : { "Content-Type": "application/json" }),
        ...(options.authenticated === false || !token
          ? {}
          : { Authorization: `Bearer ${token}` }),
      },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  }

  private async errorMessage(response: Response) {
    try {
      const payload = await response.json();
      return payload.detail || payload.message || response.statusText;
    } catch {
      return response.statusText || "Request failed";
    }
  }
}

export const api = new ApiClient();
