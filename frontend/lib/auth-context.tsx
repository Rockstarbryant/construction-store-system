"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, clearTokens, getAccessToken, setTokens } from "./api";
import type { CurrentUser, Site } from "./types";

const ACTIVE_SITE_KEY = "css_active_site_id";

interface AuthContextValue {
  user: CurrentUser | null;
  loading: boolean;
  sites: Site[];
  activeSiteId: string | null;
  setActiveSiteId: (id: string) => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshSites: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [sites, setSites] = useState<Site[]>([]);
  const [activeSiteId, setActiveSiteIdState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const setActiveSiteId = useCallback((id: string) => {
    setActiveSiteIdState(id);
    window.localStorage.setItem(ACTIVE_SITE_KEY, id);
  }, []);

  const refreshSites = useCallback(async () => {
    try {
      const list = await api.get<Site[]>("/sites");
      setSites(list);
      const stored = window.localStorage.getItem(ACTIVE_SITE_KEY);
      if (stored && list.some((s) => s.id === stored)) {
        setActiveSiteIdState(stored);
      } else if (list.length > 0) {
        setActiveSiteIdState(list[0].id);
        window.localStorage.setItem(ACTIVE_SITE_KEY, list[0].id);
      }
    } catch {
      setSites([]);
    }
  }, []);

  useEffect(() => {
    async function bootstrap() {
      const token = getAccessToken();
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const me = await api.get<CurrentUser>("/auth/me");
        setUser(me);
        await refreshSites();
      } catch {
        clearTokens();
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    bootstrap();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokenRes = await api.public.post<{ access_token: string; refresh_token: string }>(
        "/auth/login",
        { email, password }
      );
      setTokens(tokenRes.access_token, tokenRes.refresh_token);
      const me = await api.get<CurrentUser>("/auth/me");
      setUser(me);
      await refreshSites();
      router.push("/dashboard");
    },
    [router, refreshSites]
  );

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
    setSites([]);
    setActiveSiteIdState(null);
    router.push("/login");
  }, [router]);

  const value = useMemo(
    () => ({ user, loading, sites, activeSiteId, setActiveSiteId, login, logout, refreshSites }),
    [user, loading, sites, activeSiteId, setActiveSiteId, login, logout, refreshSites]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
