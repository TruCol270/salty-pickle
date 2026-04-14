/** Backend API origin (no trailing slash). Used by Lovable/Vercel and local Vite. */
function normalizeApiBase(raw: string | undefined): string {
  return (raw ?? '').trim().replace(/\/$/, '');
}

/**
 * Resolve public API base URL from env. Prefer `VITE_API_BASE_URL`; fall back to
 * `VITE_PUBLIC_API_URL` for templates that use that name.
 */
export function getApiBaseUrl(): string {
  return (
    normalizeApiBase(import.meta.env.VITE_API_BASE_URL) ||
    normalizeApiBase(import.meta.env.VITE_PUBLIC_API_URL)
  );
}
