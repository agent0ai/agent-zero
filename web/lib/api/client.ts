const BASE = '/api/backend'

let csrfToken: string | null = null

async function ensureCsrf(): Promise<string> {
  if (csrfToken) return csrfToken
  const res = await fetch(`${BASE}/csrf_token`, { method: 'POST' })
  if (res.ok) {
    const data = await res.json()
    csrfToken = data.token || ''
  }
  return csrfToken || ''
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body: unknown,
  ) {
    super(`API ${status}: ${statusText}`)
    this.name = 'ApiError'
  }
}

export async function api<T = unknown>(
  path: string,
  options: {
    method?: string
    body?: unknown
    params?: Record<string, string>
  } = {},
): Promise<T> {
  const { method = 'POST', body, params } = options

  const url = new URL(`${BASE}/${path}`, window.location.origin)
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      url.searchParams.set(k, v)
    }
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (method !== 'GET') {
    headers['X-CSRF-Token'] = await ensureCsrf()
  }

  const res = await fetch(url.toString(), {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: 'same-origin',
  })

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    let parsed: unknown = text
    try { parsed = JSON.parse(text) } catch {}
    throw new ApiError(res.status, res.statusText, parsed)
  }

  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return res.json() as Promise<T>
  }

  return res.text() as unknown as T
}

export function resetCsrf() {
  csrfToken = null
}
