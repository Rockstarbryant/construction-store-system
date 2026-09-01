import type { ApiErrorBody } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_PREFIX = `${API_BASE}/api/v1`;

const ACCESS_TOKEN_KEY = "css_access_token";
const REFRESH_TOKEN_KEY = "css_refresh_token";

export class ApiError extends Error {
  status: number;
  fieldErrors?: { loc: (string | number)[]; msg: string }[];

  constructor(status: number, message: string, fieldErrors?: ApiErrorBody["errors"]) {
    super(message);
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(access: string, refresh: string) {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, access);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function clearTokens() {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

async function parseErrorBody(res: Response): Promise<ApiError> {
  let body: ApiErrorBody = {};
  try {
    body = await res.json();
  } catch {
    // no JSON body
  }
  const message =
    body.detail ?? body.errors?.map((e) => e.msg).join(" ") ?? `Request failed (${res.status})`;
  return new ApiError(res.status, message, body.errors);
}

let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const refresh_token = getRefreshToken();
  if (!refresh_token) return false;
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_PREFIX}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token }),
    })
      .then(async (res) => {
        if (!res.ok) return false;
        const data = await res.json();
        setTokens(data.access_token, data.refresh_token);
        return true;
      })
      .catch(() => false)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  authenticated?: boolean;
}

async function request<T>(path: string, opts: RequestOptions = {}, isRetry = false): Promise<T> {
  const { method = "GET", body, authenticated = true } = opts;
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (authenticated) {
    const token = getAccessToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_PREFIX}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && authenticated && !isRetry) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      return request<T>(path, opts, true);
    }
    clearTokens();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new ApiError(401, "Session expired. Please log in again.");
  }

  if (!res.ok) {
    throw await parseErrorBody(res);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: "PATCH", body }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  public: {
    post: <T>(path: string, body?: unknown) =>
      request<T>(path, { method: "POST", body, authenticated: false }),
  },
};
