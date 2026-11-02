export class ApiError extends Error {
  readonly status: number
  readonly detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function readDetail(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body?.detail === 'string') return body.detail
    // FastAPI validation errors: a list of {msg} objects, e.g. "Value error, unknown channel: fax".
    if (Array.isArray(body?.detail)) {
      const messages = body.detail
        .map((item: { msg?: unknown }) => item?.msg)
        .filter((msg: unknown): msg is string => typeof msg === 'string')
        .map((msg: string) => msg.replace(/^Value error, /, ''))
      if (messages.length) return messages.join('. ')
    }
  } catch {
    // Body was empty or not JSON; fall back to the status text.
  }
  return response.statusText || `Request failed with status ${response.status}`
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    credentials: 'same-origin',
    ...init,
    headers: { 'Content-Type': 'application/json', Accept: 'application/json', ...init.headers },
  })
  if (!response.ok) {
    throw new ApiError(response.status, await readDetail(response))
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
