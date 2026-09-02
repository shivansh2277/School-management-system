import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { api, tokenStore } from "../api/client";

export type Me = {
  user: { id: number; role: string; full_name: string; login_id: string };
};

type AuthValue = {
  me: Me | null;
  loading: boolean;
  login: (loginId: string, password: string) => Promise<void>;
  logout: () => void;
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
      .get<Me>("/auth/me")
      .then(setMe)
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  const login = async (loginId: string, password: string) => {
    // The dashboard always logs in through the admin tab; the API rejects any
    // other role on these credentials (BLUEPRINT section 10).
    const res = await api.post<{ access_token: string }>("/auth/login", {
      role: "admin",
      login_id: loginId,
      password,
    });
    tokenStore.set(res.access_token);
    setMe(await api.get<Me>("/auth/me"));
  };

  const logout = () => {
    tokenStore.clear();
    setMe(null);
  };

  return <Ctx.Provider value={{ me, loading, login, logout }}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const value = useContext(Ctx);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
