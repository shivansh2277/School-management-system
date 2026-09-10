import { useQueryClient } from "@tanstack/react-query";
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
  /**
   * Re-read /auth/me.
   *
   * The module switches on /configuration change what `modules` contains, and
   * the sidebar is derived from it - so without this the clerk turns a module
   * off, watches nothing happen, and reasonably concludes the switch is
   * broken. The API honours it immediately; only this cached copy is stale.
   */
  refresh: () => Promise<void>;
  can: (permission: string) => boolean;
  hasModule: (code: string) => boolean;
};

const Ctx = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  // AuthProvider sits inside QueryClientProvider (main.tsx), so this is the
  // cache every screen reads through.
  const qc = useQueryClient();

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

  const refresh = async () => {
    setMe((await api.get("/auth/me")) as Me);
  };

  const logout = () => {
    tokenStore.clear();
    setMe(null);
    /**
     * Drop every cached response, not just the token.
     *
     * The query cache outlived the session, so the next person to sign in on
     * the same browser was served the previous one's data before their own
     * request returned - and for a query their role is not allowed to make at
     * all, it never returned, so the stale answer simply stood. A fee counter
     * was shown the admin's class list this way, which is the permission gate
     * being bypassed by cache rather than by the API.
     *
     * That is not hypothetical here: the counter PC in a school office is
     * shared, and signing out so a colleague can sign in is the normal way it
     * is used.
     */
    qc.clear();
  };

  const value = useMemo<AuthValue>(() => {
    const held = new Set(me?.permissions ?? []);
    const on = new Set(me?.modules ?? []);
    return {
      me,
      loading,
      login,
      logout,
      refresh,
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
