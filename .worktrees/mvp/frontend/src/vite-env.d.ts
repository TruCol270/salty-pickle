/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Preferred: HTTPS origin of the FastAPI service (e.g. https://api.example.com). */
  readonly VITE_API_BASE_URL?: string;
  /** Optional alias used by some templates; ignored if VITE_API_BASE_URL is set. */
  readonly VITE_PUBLIC_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
