/** The only HTTP code in the web client, typed against the generated schema. */
import type { paths } from "./schema";
import { ApiError } from "./errors";

export { ApiError };

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "sunrise.token";
const REFRESH_KEY = "sunrise.refresh";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access: string, refresh?: string) => {
    localStorage.setItem(TOKEN_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

/** Paths that support a given method, as literal strings from the schema. */
type GetPaths = { [P in keyof paths]: paths[P] extends { get: unknown } ? P : never }[keyof paths];
type PostPaths = { [P in keyof paths]: paths[P] extends { post: unknown } ? P : never }[keyof paths];
type PatchPaths = { [P in keyof paths]: paths[P] extends { patch: unknown } ? P : never }[keyof paths];
type PutPaths = { [P in keyof paths]: paths[P] extends { put: unknown } ? P : never }[keyof paths];
type DeletePaths = { [P in keyof paths]: paths[P] extends { delete: unknown } ? P : never }[keyof paths];

/**
 * The JSON request body of one operation, or `undefined` where it takes none.
 *
 * `Ok<>` below has typed responses since Slice 0; bodies stayed `unknown`, so a
 * write with a misspelled or wrongly shaped field compiled cleanly and failed
 * at runtime - the exact defect the generated schema exists to prevent. The
 * generator already emits `requestBody` for routes that take one and
 * `requestBody?: never` for routes that do not, which is what separates the
 * two branches here.
 */
type Body<T> = T extends { requestBody: { content: { "application/json": infer B } } }
  ? B
  : undefined;

/**
 * The body argument, present only when the route actually takes one.
 *
 * A plain `body?: Body<...>` would catch a wrong shape but still let a required
 * body be omitted entirely, which is the same runtime 422 by a shorter route.
 */
type BodyArg<T> = Body<T> extends undefined ? [] : [body: Body<T>];

/** The 200 body of one operation. `unknown` where the route is untyped. */
type Ok<T> = T extends { responses: { 200: { content: { "application/json": infer R } } } }
  ? R
  : T extends { responses: { 201: { content: { "application/json": infer R } } } }
    ? R
    : unknown;

/**
 * Ask the API for a new access token.
 *
 * The refresh token was previously thrown away at login, so staff were bounced
 * to the login screen whenever the access token expired
 * (ACCESS_TOKEN_EXPIRE_MINUTES = 1440). One retry, then give up: a refresh loop
 * on a genuinely dead session is worse than a login prompt.
 */
async function refreshAccessToken(): Promise<boolean> {
  const refresh_token = tokenStore.getRefresh();
  if (!refresh_token) return false;
  const res = await fetch(`${BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token }),
  });
  if (!res.ok) return false;
  const body = (await res.json()) as { access_token: string };
  tokenStore.set(body.access_token);
  return true;
}

async function send(path: string, init: RequestInit): Promise<Response> {
  const token = tokenStore.get();
  return fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
  });
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res = await send(path, init);

  if (res.status === 401 && (await refreshAccessToken())) {
    res = await send(path, init);
  }
  if (res.status === 401) {
    tokenStore.clear();
    window.location.hash = "#/login";
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/**
 * A key that makes a retried request one transaction rather than two.
 *
 * The API requires it on POST /admin/fees/payments (minimum 8 characters)
 * precisely so a double-click or a retry after a dropped connection cannot take
 * the money twice. Generate ONE key per logical transaction and reuse it across
 * retries; a fresh key per click defeats the whole mechanism.
 */
export function newIdempotencyKey(): string {
  return crypto.randomUUID().replace(/-/g, "");
}

export const api = {
  get: <P extends GetPaths>(path: P, query?: string) =>
    request<Ok<paths[P]["get"]>>(`${path}${query ?? ""}`),
  post: <P extends PostPaths>(path: P, ...args: BodyArg<paths[P]["post"]>) =>
    request<Ok<paths[P]["post"]>>(path, { method: "POST", body: JSON.stringify(args[0] ?? {}) }),
  patch: <P extends PatchPaths>(path: P, ...args: BodyArg<paths[P]["patch"]>) =>
    request<Ok<paths[P]["patch"]>>(path, { method: "PATCH", body: JSON.stringify(args[0] ?? {}) }),
  // Fourteen routes are PUT rather than PATCH, and they are the ones that
  // replace a whole list wherever a partial update would be meaningless: a
  // grading ladder, a route's stops, an application's guardians, the module
  // switches on /admin/configuration.
  put: <P extends PutPaths>(path: P, ...args: BodyArg<paths[P]["put"]>) =>
    request<Ok<paths[P]["put"]>>(path, { method: "PUT", body: JSON.stringify(args[0] ?? {}) }),
  // Takes a query string for the same reason `get` does: DELETE
  // /admin/notices/{id} needs the audit reason, and a DELETE body is accepted
  // by FastAPI but not by every proxy in front of it.
  del: <P extends DeletePaths>(path: P, query?: string) =>
    request<Ok<paths[P]["delete"]>>(`${path}${query ?? ""}` as P, { method: "DELETE" }),
};

/**
 * Money arrives from the API as a string and stays one.
 *
 * `Numeric` is serialised as a string deliberately; parsing it into a JS number
 * puts a concession a paisa away from the printed fee card. This formats for
 * display and nothing else ever converts.
 */
// Intl.NumberFormat#format uses ToIntlMathematicalValue on a string argument,
// which parses it as an exact decimal rather than coercing through a 64-bit
// float (ToNumber) the way Number(v) or template-literal interpolation would.
// Passing the string straight through is what keeps the guarantee above true.
const moneyFormat = new Intl.NumberFormat("en-IN", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
// TS's lib.d.ts types NumberFormat#format as number|bigint only (the string
// overload lives in lib.es2023.intl, which this project's ES2022 lib target
// doesn't pull in) even though the runtime accepts a numeric string and, per
// the comment above, that's exactly the path that avoids the float.
export const money = (v: string | number) => `₹${moneyFormat.format(v as number)}`;
