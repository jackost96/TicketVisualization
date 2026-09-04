const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
const TOKEN_STORAGE_KEY = "auth_token";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

/** Turns a caught error into a user-displayable message. Shows the real message for both API
 * errors (e.g. "Incorrect email or password") and unexpected JS errors (e.g. a bug like a
 * malformed URL) rather than collapsing everything to a generic fallback -- makes bugs visible
 * instead of hiding them behind "Something went wrong". */
export function getErrorMessage(err: unknown, fallback = "Something went wrong"): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return fallback;
}

let authToken: string | null = localStorage.getItem(TOKEN_STORAGE_KEY);
let onUnauthorized: (() => void) | null = null;

export function setAuthToken(token: string | null): void {
  authToken = token;
  if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
  else localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export function getAuthToken(): string | null {
  return authToken;
}

export function setUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler;
}

type QueryValue = string | number | boolean | undefined | null;

interface RequestOptions {
  method?: string;
  body?: unknown;
  form?: Record<string, string>;
  query?: Record<string, QueryValue>;
}

function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  // Base is needed because API_BASE_URL may be relative (e.g. "/api/v1" in the Docker build,
  // so nginx can same-origin proxy it) -- `new URL(relativePath)` throws without one. Absolute
  // API_BASE_URL values (native dev's "http://localhost:8000/api/v1") just ignore the base.
  const url = new URL(API_BASE_URL.replace(/\/$/, "") + path, window.location.origin);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, form, query } = options;
  const headers: Record<string, string> = {};
  const wasAuthenticated = Boolean(authToken);
  if (authToken) headers.Authorization = `Bearer ${authToken}`;

  let requestBody: BodyInit | undefined;
  if (form) {
    requestBody = new URLSearchParams(form);
    headers["Content-Type"] = "application/x-www-form-urlencoded";
  } else if (body !== undefined) {
    requestBody = JSON.stringify(body);
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(buildUrl(path, query), { method, headers, body: requestBody });

  // A 401 on a request that carried a token means that token is no longer valid -- a genuine
  // session expiry. A 401 on a request with no token (e.g. a login attempt with wrong
  // credentials) isn't a session expiring, it's just a rejected request -- fall through to the
  // normal error-detail handling below so the real reason (e.g. "Incorrect email or password")
  // reaches the user instead of a misleading "Session expired".
  if (response.status === 401 && wasAuthenticated) {
    setAuthToken(null);
    onUnauthorized?.();
    throw new ApiError(401, null, "Session expired");
  }

  if (!response.ok) {
    let detail: unknown = null;
    try {
      detail = await response.json();
    } catch {
      // response had no JSON body
    }
    const detailMessage =
      detail && typeof detail === "object" && "detail" in detail
        ? String((detail as { detail: unknown }).detail)
        : undefined;
    throw new ApiError(response.status, detail, detailMessage ?? response.statusText ?? "Request failed");
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
