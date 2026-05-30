/**
 * Weather1 — API base URL helper
 *
 * Local development (NEXT_PUBLIC_API_BASE_URL not set):
 *   apiUrl('/markets/weather') → '/api/markets/weather'
 *   Next.js rewrites /api/* → http://localhost:8000/*
 *
 * Production (NEXT_PUBLIC_API_BASE_URL=https://weather1-polymarket-production.up.railway.app):
 *   apiUrl('/markets/weather') → 'https://...railway.app/markets/weather'
 *   Calls Railway backend directly (CORS: Vercel .app domains are whitelisted).
 *
 * Usage: fetch(apiUrl('/markets/weather'))
 *        fetch(`${apiUrl('/signals/latest')}?limit=50`)
 *
 * NEVER commit a .env.local or .env.production with real values.
 * See frontend/.env.example for the template.
 */

const _base = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").replace(/\/$/, "");

/**
 * Build a full API URL.
 * @param path — must start with "/" e.g. "/markets/weather"
 */
export function apiUrl(path: string): string {
  if (_base) {
    // Production: direct absolute URL to Railway backend
    return `${_base}${path}`;
  }
  // Local dev: relative path proxied by Next.js rewrites
  return `/api${path}`;
}
