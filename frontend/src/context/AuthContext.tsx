import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import {
  clearAuthSession,
  consumeAuthFromUrl,
  persistAuthSession,
  readStoredToken,
  readStoredUserId,
} from '../lib/authSession';

interface AuthContextValue {
  isAuthenticated: boolean;
  userId: number | null;
  login: (token: string, userId?: number) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => readStoredToken());
  const [userId, setUserId] = useState<number | null>(() => readStoredUserId());

  useEffect(() => {
    const authFromUrl = consumeAuthFromUrl();
    if (authFromUrl) {
      const resolvedUserId = persistAuthSession(
        authFromUrl.token,
        authFromUrl.userId
      );
      setToken(authFromUrl.token);
      setUserId(resolvedUserId);
    }
  }, []);

  const login = useCallback((newToken: string, nextUserId?: number) => {
    const resolvedUserId = persistAuthSession(newToken, nextUserId ?? null);
    setToken(newToken);
    setUserId(resolvedUserId);
  }, []);

  const logout = useCallback(() => {
    clearAuthSession();
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
