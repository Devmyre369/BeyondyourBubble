
import axios, {
  type InternalAxiosRequestConfig,
} from 'axios'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  'http://127.0.0.1:8000/api'

const ACCESS_TOKEN_KEY = 'byb_access_token'
const REFRESH_TOKEN_KEY = 'byb_refresh_token'
const USER_KEY = 'byb_user'

interface RefreshResponse {
  access: string
  refresh?: string
}

interface RetryableRequestConfig
  extends InternalAxiosRequestConfig {
  _retry?: boolean
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Only one refresh operation can run at a time.
let refreshPromise: Promise<string> | null = null
let sessionInvalidated = false

function clearSession() {
  const hadSession = Boolean(
    sessionStorage.getItem(ACCESS_TOKEN_KEY) ||
    sessionStorage.getItem(REFRESH_TOKEN_KEY) ||
    sessionStorage.getItem(USER_KEY),
  )
  sessionStorage.removeItem(ACCESS_TOKEN_KEY)
  sessionStorage.removeItem(REFRESH_TOKEN_KEY)
  sessionStorage.removeItem(USER_KEY)

  sessionInvalidated = true
  if (hadSession) {
    // Wait until provider effects have registered their listeners during the
    // initial React mount (StrictMode mounts effects after child effects).
    window.setTimeout(() => {
      if (!sessionStorage.getItem(ACCESS_TOKEN_KEY)) {
        window.dispatchEvent(new Event('byb:auth-expired'))
      }
    }, 0)
  }
}

function tokenIsExpired(token: string | null): boolean {
  if (!token) return true

  try {
    const payload = token.split('.')[1]
    if (!payload) return true
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    const claims = JSON.parse(
      window.atob(base64.padEnd(Math.ceil(base64.length / 4) * 4, '=')),
    ) as { exp?: unknown }
    return typeof claims.exp !== 'number' || claims.exp <= Date.now() / 1000 + 15
  } catch {
    return true
  }
}

async function performTokenRefresh(): Promise<string> {
  const currentRefreshToken =
    sessionStorage.getItem(REFRESH_TOKEN_KEY)

  if (!currentRefreshToken) {
    throw new Error('Refresh token is missing')
  }

  // Use plain axios to avoid triggering this API client's
  // response interceptor recursively.
  const response = await axios.post<RefreshResponse>(
    `${API_BASE_URL.replace(/\/+$/, '')}/accounts/token/refresh/`,
    {
      refresh: currentRefreshToken,
    },
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )

  const newAccessToken = response.data.access

  if (!newAccessToken) {
    throw new Error('Access token was not returned')
  }

  // Save the new access token.
  sessionStorage.setItem(
    ACCESS_TOKEN_KEY,
    newAccessToken
  )

  // SimpleJWT may return a rotated refresh token.
  // Always replace the old one when a new one is returned.
  const newRefreshToken =
    response.data.refresh || currentRefreshToken

  sessionStorage.setItem(
    REFRESH_TOKEN_KEY,
    newRefreshToken
  )

  // Keep React's authentication context synchronized.
  window.dispatchEvent(
    new CustomEvent('byb:tokens-refreshed', {
      detail: {
        access: newAccessToken,
        refresh: newRefreshToken,
      },
    })
  )

  return newAccessToken
}

function getRefreshedAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = performTokenRefresh().finally(() => {
      refreshPromise = null
    })
  }

  return refreshPromise
}

// Refresh expired JWTs before starting protected requests. If both tokens
// have expired, clear the stale session without sending doomed API calls.
api.interceptors.request.use(async (config) => {
  const requestUrl = config.url || ''
  const authEndpoints = [
    '/accounts/token/refresh/',
    '/accounts/login/',
    '/accounts/signup/',
    '/accounts/verify-signup/',
    '/accounts/password-reset/',
  ]
  const isAuthEndpoint = authEndpoints.some((endpoint) =>
    requestUrl.includes(endpoint),
  )

  let accessToken =
    sessionStorage.getItem(ACCESS_TOKEN_KEY)

  if (!isAuthEndpoint && sessionInvalidated) {
    if (accessToken) {
      // A successful login has stored a fresh token since the old session
      // was invalidated.
      sessionInvalidated = false
    } else {
      throw new axios.CanceledError('Please sign in to continue.')
    }
  }

  if (!isAuthEndpoint && accessToken && tokenIsExpired(accessToken)) {
    const refreshToken = sessionStorage.getItem(REFRESH_TOKEN_KEY)
    if (tokenIsExpired(refreshToken)) {
      clearSession()
      throw new axios.CanceledError('Your session has expired. Please sign in again.')
    }

    try {
      accessToken = await getRefreshedAccessToken()
    } catch {
      clearSession()
      throw new axios.CanceledError('Your session has expired. Please sign in again.')
    }
  }

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }

  // Allow Axios to automatically set multipart/form-data
  // with the correct boundary when uploading files.
  if (
    typeof FormData !== 'undefined' &&
    config.data instanceof FormData
  ) {
    config.headers.delete('Content-Type')
  }

  return config
})

// Automatically refresh expired access tokens.
api.interceptors.response.use(
  (response) => response,

  async (error) => {
    const originalRequest =
      error.config as RetryableRequestConfig | undefined

    if (!originalRequest || error.response?.status !== 401) {
      return Promise.reject(error)
    }

    const requestUrl = originalRequest.url || ''

    // Never attempt to refresh the refresh endpoint itself,
    // or authentication endpoints such as login and signup.
    const excludedEndpoints = [
      '/accounts/token/refresh/',
      '/accounts/login/',
      '/accounts/signup/',
      '/accounts/verify-signup/',
      '/accounts/password-reset/',
    ]

    if (
      excludedEndpoints.some((endpoint) =>
        requestUrl.includes(endpoint)
      )
    ) {
      return Promise.reject(error)
    }

    // Prevent infinite retry loops.
    if (originalRequest._retry) {
      return Promise.reject(error)
    }

    // Only refresh when the original request had a bearer token.
    const authorization =
      originalRequest.headers.Authorization

    if (!authorization) {
      return Promise.reject(error)
    }

    originalRequest._retry = true

    try {
      const newAccessToken =
        await getRefreshedAccessToken()

      originalRequest.headers.Authorization =
        `Bearer ${newAccessToken}`

      // Retry the original request with the new token.
      return api(originalRequest)
    } catch (refreshError) {
      clearSession()

      return Promise.reject(refreshError)
    }
  }
)

export default api
