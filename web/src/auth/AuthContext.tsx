import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, tokenStore } from "../api/client";

/**
 * Everything /auth/me returns. The previous version declared only `user` and
 * discarded the rest, which is why every role saw the same nine menu items -
 * MeOut's own comment says the clients are meant to render navigation from
 * these.
 */
export type Me = {
  user: { id: number; role: string; full_name: string; login_id: string };
  permissions: string[];
  roles: string[];
  school_code: string | null;
  school_name: string | null;
  academic_year: string | null;
  modules: string[];
};

type AuthValue = {
  me: Me | null;
  loading: boolean;
  login: (loginId: string, password: string) => Promise<void>;
  logout: () => void;
  can: (permission: string) => boolean;
  hasModule: (code: string) => boolean;
};

const Ctx = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tokenStore.get()) {
      setLoading(false);
      return;
    }
    api
      .get("/auth/me")
      .then((m) => setMe(m as Me))
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  const login = async (loginId: string, password: string) => {
    // Staff log in through the admin tab: the office, accountant, principal,
    // exam controller and transport manager are all users.role == admin.
    // Teachers, students and guardians use the mobile app (spec section 3.5).
    const res = await api.post("/auth/login", {
      role: "admin",
      login_id: loginId,
      password,
    });
    const pair = res as { access_token: string; refresh_token: string };
    tokenStore.set(pair.access_token, pair.refresh_token);
    setMe((await api.get("/auth/me")) as Me);
  };

  const logout = () => {
    tokenStore.clear();
    setMe(null);
  };

  const value = useMemo<AuthValue>(() => {
    const held = new Set(me?.permissions ?? []);
    const on = new Set(me?.modules ?? []);
    return {
      me,
      loading,
      login,
      logout,
      can: (permission) => held.has(permission),
      hasModule: (code) => on.has(code),
    };
  }, [me, loading]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const value = useContext(Ctx);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
