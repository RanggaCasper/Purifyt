/**
 * Standard API response envelope from Purifyt backend.
 */
export interface ApiResponse<T = unknown> {
  status: boolean
  data: T | null
  message: string
  errors: Record<string, unknown> | null
  timestamp: string
}

/**
 * Paginated data wrapper returned inside ApiResponse.data.
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

/**
 * Custom error thrown by apiFetch when status === false
 * or the HTTP request itself fails.
 */
export class ApiError extends Error {
  readonly statusCode: number | undefined
  readonly errors: Record<string, unknown> | null
  readonly timestamp: string

  constructor(
    message: string,
    errors: Record<string, unknown> | null = null,
    timestamp = '',
    statusCode?: number
  ) {
    super(message)
    this.name = 'ApiError'
    this.errors = errors
    this.timestamp = timestamp
    this.statusCode = statusCode
  }
}

let refreshPromise: Promise<boolean> | null = null

const NO_RETRY_PATHS = ['/auth/login', '/auth/refresh', '/auth/register', '/auth/logout']

/**
 * Composable for API calls with automatic Authorization header,
 * ApiResponse envelope unwrapping, and transparent 401 -> refresh -> retry.
 *
 * The access token is read from useAuth() composable (memory-only).
 * Every request includes `credentials: 'include'` so the browser
 * sends the HttpOnly refresh cookie when needed.
 */
export function useApi() {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase as string
  const auth = useAuth()

  function unwrap<T>(response: ApiResponse<T>): T {
    if (!response.status) {
      throw new ApiError(
        response.message || 'An error occurred',
        response.errors,
        response.timestamp
      )
    }
    return response.data as T
  }

  function doRefresh(): Promise<boolean> {
    if (refreshPromise) return refreshPromise

    refreshPromise = auth.refresh().finally(() => {
      refreshPromise = null
    })

    return refreshPromise
  }

  function shouldRetry(url: string): boolean {
    return !NO_RETRY_PATHS.some(p => url.includes(p))
  }

  async function apiFetch<T>(
    url: string,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    options: Record<string, any> = {}
  ): Promise<T> {
    function buildHeaders(): Record<string, string> {
      const h: Record<string, string> = { ...options.headers }
      if (auth.accessToken.value) {
        h.Authorization = `Bearer ${auth.accessToken.value}`
      }
      return h
    }

    async function execute(hdrs: Record<string, string>): Promise<T> {
      let raw: ApiResponse<T>

      try {
        raw = await $fetch<ApiResponse<T>>(`${baseURL}${url}`, {
          ...options,
          headers: hdrs,
          credentials: 'include'
        })
      } catch (fetchError: unknown) {
        const err = fetchError as { data?: ApiResponse<T>, statusMessage?: string, statusCode?: number, status?: number, message?: string }
        // $fetch puts the response body in fetchError.data
        const body: ApiResponse<T> | undefined = err?.data
        if (body && typeof body === 'object' && 'status' in body) {
          throw new ApiError(
            body.message || err?.statusMessage || 'Request failed',
            body.errors ?? null,
            body.timestamp ?? '',
            err?.statusCode
          )
        }
        const isNetworkError = !err?.statusCode && !err?.status
        throw new ApiError(
          err?.statusMessage || (isNetworkError ? 'Cannot connect to server. Please try again later.' : err?.message) || 'Network error',
          null,
          '',
          err?.statusCode
        )
      }

      return unwrap(raw)
    }

    // First attempt
    try {
      return await execute(buildHeaders())
    } catch (error: unknown) {
      const err = error as ApiError
      // On 401, try a single silent refresh (skip auth endpoints to avoid loops)
      if (err?.statusCode === 401 && shouldRetry(url)) {
        const ok = await doRefresh()
        if (ok) return await execute(buildHeaders())
        // refresh failed -> redirect to login
        navigateTo('/login')
      }
      throw err
    }
  }

  async function apiStream(
    url: string,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    body: Record<string, any>,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onEvent: (event: any) => void,
    onError?: (error: unknown) => void
  ) {
    function streamHeaders(token: string | null): Record<string, string> {
      const h: Record<string, string> = { 'Content-Type': 'application/json' }
      if (token) h.Authorization = `Bearer ${token}`
      return h
    }

    async function readSSE(response: Response) {
      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let currentEventName = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEventName = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            try {
              const parsed = JSON.parse(line.slice(6))
              if (currentEventName && !parsed.type) {
                parsed.type = currentEventName
              }
              onEvent(parsed)
            } catch { /* skip malformed SSE */ }
            currentEventName = ''
          }
        }
      }
    }

    try {
      let response = await fetch(`${baseURL}${url}`, {
        method: 'POST',
        headers: streamHeaders(auth.accessToken.value),
        credentials: 'include',
        body: JSON.stringify(body)
      })

      // 401 -> try refresh once, then retry
      if (response.status === 401 && shouldRetry(url)) {
        const ok = await doRefresh()
        if (ok) {
          response = await fetch(`${baseURL}${url}`, {
            method: 'POST',
            headers: streamHeaders(auth.accessToken.value),
            credentials: 'include',
            body: JSON.stringify(body)
          })
        }
        if (!response.ok) {
          navigateTo('/login')
          throw new ApiError('Unauthorized', null, '', 401)
        }
      }

      if (!response.ok) {
        const text = await response.text().catch(() => '')
        let message = `HTTP ${response.status}`
        try {
          const json: ApiResponse = JSON.parse(text)
          message = json.message || message
        } catch { /* ignore */ }
        throw new ApiError(message, null, '', response.status)
      }

      await readSSE(response)
    } catch (error) {
      onError?.(error)
    }
  }

  return { apiFetch, apiStream, baseURL }
}
