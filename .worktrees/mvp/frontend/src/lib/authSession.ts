export const ACCESS_TOKEN_KEY = 'access_token';
export const USER_ID_KEY = 'user_id';

export type AuthStorage = 'session' | 'local';

function getStorage(storage: AuthStorage): Storage | null {
  if (typeof window === 'undefined') return null;
  try {
    return storage === 'local' ? window.localStorage : window.sessionStorage;
  } catch {
    return null;
  }
}

function parseNumeric(value: string | null): number | null {
  if (!value) return null;
  const n = Number.parseInt(value, 10);
  return Number.isFinite(n) ? n : null;
}

function parseHashParams(hash: string): URLSearchParams {
  const raw = hash.startsWith('#') ? hash.slice(1) : hash;
  return new URLSearchParams(raw);
}

/** Read `sub` from a JWT payload (client-side only; no signature verification). */
export function parseJwtSub(token: string): number | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const payloadB64 = parts[1]
      .replace(/-/g, '+')
      .replace(/_/g, '/')
      .padEnd(Math.ceil(parts[1].length / 4) * 4, '=');
    const payload = JSON.parse(
      atob(payloadB64)
    ) as { sub?: string | number };
    if (payload.sub == null) return null;
    const parsed =
      typeof payload.sub === 'string'
        ? Number.parseInt(payload.sub, 10)
        : Number(payload.sub);
    return Number.isFinite(parsed) && Number.isInteger(parsed) && parsed > 0
      ? parsed
      : null;
  } catch {
    return null;
  }
}

export function readStoredToken(): string | null {
  const session = getStorage('session')?.getItem(ACCESS_TOKEN_KEY);
  if (session) return session;
  return getStorage('local')?.getItem(ACCESS_TOKEN_KEY) ?? null;
}

export function readStoredUserId(): number | null {
  const session = parseNumeric(getStorage('session')?.getItem(USER_ID_KEY) ?? null);
  if (session != null) return session;
  return parseNumeric(getStorage('local')?.getItem(USER_ID_KEY) ?? null);
}

export function persistAuthSession(
  token: string,
  userId?: number | null,
  storage: AuthStorage = 'session'
): number | null {
  clearAuthSession();
  const targetStorage = getStorage(storage);
  if (!targetStorage) return null;

  targetStorage.setItem(ACCESS_TOKEN_KEY, token);
  const resolvedUserId = userId ?? parseJwtSub(token);
  if (resolvedUserId != null) {
    targetStorage.setItem(USER_ID_KEY, String(resolvedUserId));
  }
  return resolvedUserId ?? null;
}

export function clearAuthSession(): void {
  getStorage('session')?.removeItem(ACCESS_TOKEN_KEY);
  getStorage('session')?.removeItem(USER_ID_KEY);
  getStorage('local')?.removeItem(ACCESS_TOKEN_KEY);
  getStorage('local')?.removeItem(USER_ID_KEY);
}

export function consumeAuthFromUrl(): { token: string; userId: number | null } | null {
  if (typeof window === 'undefined') return null;

  const searchParams = new URLSearchParams(window.location.search);
  const hashParams = parseHashParams(window.location.hash);

  const token =
    searchParams.get(ACCESS_TOKEN_KEY) ?? hashParams.get(ACCESS_TOKEN_KEY);
  if (!token) return null;

  const userId =
    parseNumeric(searchParams.get(USER_ID_KEY)) ??
    parseNumeric(hashParams.get(USER_ID_KEY)) ??
    parseJwtSub(token);

  searchParams.delete(ACCESS_TOKEN_KEY);
  searchParams.delete(USER_ID_KEY);
  hashParams.delete(ACCESS_TOKEN_KEY);
  hashParams.delete(USER_ID_KEY);

  const nextSearch = searchParams.toString();
  const nextHash = hashParams.toString();
  const nextUrl =
    `${window.location.pathname}` +
    `${nextSearch ? `?${nextSearch}` : ''}` +
    `${nextHash ? `#${nextHash}` : ''}`;

  window.history.replaceState({}, '', nextUrl);
  return { token, userId };
}
