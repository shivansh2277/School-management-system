import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { api, tokenStore } from "../api/client";

export type Role = "student" | "parent" | "teacher";

export type Child = { id: number; name: string; class_label: string; admission_no: string };

export type Me = {
  user: { id: number; role: Role; full_name: string; login_id: string };
  admission_no?: string | null;
  class_label?: string | null;
  roll_no?: number | null;
  employee_id?: string | null;
  sections?: string[] | null;
  children?: Child[] | null;
};

type AuthValue = {
  me: Me | null;
  loading: boolean;
  /** The parent tab set reflects the selected child; the choice lasts the session. */
  selectedChildId: number | null;
  selectChild: (id: number) => void;
  login: (role: Role, loginId: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const Ctx = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedChildId, setSelectedChildId] = useState<number | null>(null);

  const adopt = (next: Me) => {
    setMe(next);
    if (next.children?.length) setSelectedChildId(next.children[0].id);
  };

  useEffect(() => {
    (async () => {
      const token = await tokenStore.load();
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        adopt(await api.get<Me>("/auth/me", { timeoutMs: 60_000 }));
      } catch (err: any) {
        // Only clear the stored token if the server explicitly rejects authentication (HTTP 401/403).
        // On network failure or timeout (status 0), preserve the token so users are not logged out
        // during temporary offline conditions or Render cold-start wakeups.
        if (err?.status === 401 || err?.status === 403) {
          await tokenStore.clear();
        }
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = async (role: Role, loginId: string, password: string) => {
    const res = await api.post<{ access_token: string }>(
      "/auth/login",
      { role, login_id: loginId, password },
      { timeoutMs: 60_000 }
    );
    await tokenStore.set(res.access_token);
    try {
      adopt(await api.get<Me>("/auth/me", { timeoutMs: 60_000 }));
    } catch (meErr: any) {
      if (meErr?.status === 401 || meErr?.status === 403) {
        await tokenStore.clear();
      }
      throw meErr;
    }
  };

  const logout = async () => {
    await tokenStore.clear();
    setMe(null);
    setSelectedChildId(null);
  };

  return (
    <Ctx.Provider
      value={{
        me,
        loading,
        selectedChildId,
        selectChild: setSelectedChildId,
        login,
        logout,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useAuth() {
  const value = useContext(Ctx);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
