import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

interface AuthContextValue {
  isAuthenticated: boolean;
  userId: number | null;
  login: (token: string, userId?: number) => void;
  logout: () => void;
}

const USER_ID_KEY = 'user_id';

/** Read `sub` from a JWT payload (client-side only; no signature verification). */
function parseJwtSub(token: string): number | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const payload = JSON.parse(
      atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'))
    ) as { sub?: string | number };
    const sub = payload.sub;
    if (sub == null) return null;
    return typeof sub === 'string' ? parseInt(sub, 10) : Number(sub);
  } catch {
    return null;
  }
}

function readStoredUserId(): number | null {
  const raw = sessionStorage.getItem(USER_ID_KEY);
  if (!raw) return null;
  const n = parseInt(raw, 10);
  return Number.isFinite(n) ? n : null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() =>
    sessionStorage.getItem('access_token')
  );
  const [userId, setUserId] = useState<number | null>(() => readStoredUserId());

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('access_token');
    if (urlToken) {
      sessionStorage.setItem('access_token', urlToken);
      setToken(urlToken);
      const fromJwt = parseJwtSub(urlToken);
      if (fromJwt != null) {
        sessionStorage.setItem(USER_ID_KEY, String(fromJwt));
        setUserId(fromJwt);
      }
      params.delete('access_token');
      const qs = params.toString();
      window.history.replaceState(
        {},
        '',
        `${window.location.pathname}${qs ? `?${qs}` : ''}`
      );
    }
  }, []);

  const login = useCallback((newToken: string, nextUserId?: number) => {
    sessionStorage.setItem('access_token', newToken);
    setToken(newToken);
    if (nextUserId !== undefined) {
      sessionStorage.setItem(USER_ID_KEY, String(nextUserId));
      setUserId(nextUserId);
    } else {
      const fromJwt = parseJwtSub(newToken);
      if (fromJwt != null) {
        sessionStorage.setItem(USER_ID_KEY, String(fromJwt));
        setUserId(fromJwt);
      }
    }
  }, []);

  const logout = useCallback(() => {
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem(USER_ID_KEY);
    setToken(null);
    setUserId(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: !!token,
      userId,
      login,
      logout,
    }),
    [token, userId, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>');
  }
  return ctx;
}
