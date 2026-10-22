const base = import.meta.env.VITE_API_URL || ''

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details: { row?: number; field?: string; message: string }[] = [],
  ) {
    super(message)
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('insightflow_token')
  const headers = new Headers(options.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData))
    headers.set('Content-Type', 'application/json')
  let response: Response
  try {
    response = await fetch(`${base}${path}`, { ...options, headers })
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', 'Unable to reach the server. Check your connection.')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    if (response.status === 401 && !path.includes('/auth/login')) {
      localStorage.removeItem('insightflow_token')
      sessionStorage.removeItem('insightflow_user')
    }
    throw new ApiError(
      response.status,
      body.error?.code || 'REQUEST_FAILED',
      body.error?.message || 'The request failed.',
      body.error?.details || [],
    )
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const json = (value: unknown): RequestInit => ({
  method: 'POST',
  body: JSON.stringify(value),
})
