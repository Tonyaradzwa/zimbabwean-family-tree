function inferCodespacesApiBaseUrl(): string | null {
  if (typeof window === 'undefined') return null

  const host = window.location.hostname
  const match = host.match(/^(.*)-\d+\.app\.github\.dev$/)
  if (!match) return null

  const prefix = match[1]
  return `https://${prefix}-8000.app.github.dev/api/v1`
}

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.DEV ? '/api/v1' : inferCodespacesApiBaseUrl()) ??
  'http://localhost:8000/api/v1'
