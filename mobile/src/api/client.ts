import AsyncStorage from "@react-native-async-storage/async-storage";
import Constants from "expo-constants";
import { Platform } from "react-native";

export function resolveApiBaseUrl(): string {
  const envUrl = process.env.EXPO_PUBLIC_API_URL?.trim();

  // 1. Web browser: respect explicit env or use current browser host
  if (Platform.OS === "web") {
    if (envUrl) return envUrl;
    if (typeof window !== "undefined" && window.location?.hostname) {
      return `http://${window.location.hostname}:8000`;
    }
    return "http://127.0.0.1:8000";
  }

  // 2. Explicit custom non-loopback env URL (e.g. production/staging or specific LAN override)
  if (envUrl && !envUrl.includes("127.0.0.1") && !envUrl.includes("localhost")) {
    return envUrl;
  }

  // 3. Dynamic Expo packager host detection for physical devices & emulators
  // Expo sets hostUri (e.g. "192.168.29.227:8081") during development
  const hostUri =
    Constants.expoConfig?.hostUri ??
    (Constants as any).manifest2?.extra?.expoGo?.debuggerHost ??
    (Constants as any).expoGoConfig?.debuggerHost;

  if (hostUri) {
    const host = hostUri.split(":")[0];
    if (host && host !== "localhost" && host !== "127.0.0.1") {
      return `http://${host}:8000`;
    }
  }

  // 4. Fallback URL parsing from experienceUrl or linkingUri
  const fallbackUrl = Constants.experienceUrl || Constants.linkingUri;
  if (fallbackUrl) {
    try {
      const parsed = new URL(fallbackUrl);
      if (parsed.hostname && parsed.hostname !== "localhost" && parsed.hostname !== "127.0.0.1") {
        return `http://${parsed.hostname}:8000`;
      }
    } catch {}
  }

  // 5. Explicit env if provided (even if loopback)
  if (envUrl) {
    return envUrl;
  }

  // 6. Android emulator loopback alias (10.0.2.2 maps to host PC loopback)
  if (Platform.OS === "android") {
    return "http://10.0.2.2:8000";
  }

  // 7. Default loopback (iOS simulator or local desktop)
  return "http://127.0.0.1:8000";
}

const BASE = resolveApiBaseUrl();
const TOKEN_KEY = "sunrise.token";

let memoryToken: string | null = null;

export const tokenStore = {
  get: () => memoryToken,
  load: async () => {
    memoryToken = await AsyncStorage.getItem(TOKEN_KEY);
    return memoryToken;
  },
  set: async (t: string) => {
    memoryToken = t;
    await AsyncStorage.setItem(TOKEN_KEY, t);
  },
  clear: async () => {
    memoryToken = null;
    await AsyncStorage.removeItem(TOKEN_KEY);
  },
};

export class ApiError extends Error {
  constructor(readonly status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(memoryToken ? { Authorization: `Bearer ${memoryToken}` } : {}),
      ...(init.headers ?? {}),
    },
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, detail.detail ?? res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  base: BASE,
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body ?? {}) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body ?? {}) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  token: () => memoryToken,
};

export const money = (v: string | number) =>
  `\u20b9${Number(v).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;

/**
 * Formats ISO date or Date object to standardized DD-MM-YYYY.
 * Example: '2026-08-21' -> '21-08-2026'
 */
export function formatDate(input: string | Date | null | undefined): string {
  if (!input) return "-";
  if (typeof input === "string") {
    const trimmed = input.trim();
    // Fast path for ISO YYYY-MM-DD
    if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
      const [y, m, d] = trimmed.split("-");
      return `${d}-${m}-${y}`;
    }
  }
  const d = typeof input === "string" ? new Date(input) : input;
  if (isNaN(d.getTime())) return String(input);
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = d.getFullYear();
  return `${day}-${month}-${year}`;
}
