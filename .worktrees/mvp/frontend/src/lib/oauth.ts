import { api } from './api';
import { getApiBaseUrl } from './env';

type Provider = 'strava' | 'google' | 'whoop';
type AuthenticatedProvider = 'google' | 'whoop';

function normalizedApiBaseUrl(): string {
  return getApiBaseUrl();
}

export function buildOAuthAuthorizeUrl(
  provider: Provider,
  redirectPath: string
): string {
  const redirectUrl = new URL(redirectPath, window.location.origin).toString();
  const params = new URLSearchParams({ redirect_url: redirectUrl });

  const base = normalizedApiBaseUrl();
  const path = `/auth/${provider}/authorize`;
  return `${base}${path}?${params.toString()}`;
}

export async function requestOAuthAuthorizeUrl(
  provider: AuthenticatedProvider,
  redirectPath: string
): Promise<string> {
  const redirectUrl = new URL(redirectPath, window.location.origin).toString();
  const response = await api.post<{ auth_url: string }>(`/auth/${provider}/authorize-url`, {
    redirect_url: redirectUrl,
  });
  return response.data.auth_url;
}
