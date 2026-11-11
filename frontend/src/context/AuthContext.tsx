
import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import type { AuthUser, AuthResponse } from '../services/authApi'

interface AuthContextType {
  user: AuthUser | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  completeAuthentication: (data: AuthResponse) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const ACCESS_TOKEN_KEY = 'byb_access_token'
const REFRESH_TOKEN_KEY = 'byb_refresh_token'
const USER_KEY = 'byb_user'

function getStoredUser(): AuthUser | null {
  try {
    const storedUser = sessionStorage.getItem(USER_KEY)
    return storedUser ? JSON.parse(storedUser) as AuthUser : null
  } catch {
    return null
  }
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(getStoredUser)

  const [accessToken, setAccessToken] = useState<string | null>(
    () => sessionStorage.getItem(ACCESS_TOKEN_KEY)
  )

  const [refreshToken, setRefreshToken] = useState<string | null>(
    () => sessionStorage.getItem(REFRESH_TOKEN_KEY)
  )

  const completeAuthentication = (data: AuthResponse) => {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, data.tokens.access)
    sessionStorage.setItem(REFRESH_TOKEN_KEY, data.tokens.refresh)
    sessionStorage.setItem(USER_KEY, JSON.stringify(data.user))

    setAccessToken(data.tokens.access)
    setRefreshToken(data.tokens.refresh)
    setUser(data.user)
  }

  const logout = () => {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY)
    sessionStorage.removeItem(REFRESH_TOKEN_KEY)
    sessionStorage.removeItem(USER_KEY)

    setAccessToken(null)
    setRefreshToken(null)
    setUser(null)
  }

  const value = useMemo(
    () => ({
      user,
      accessToken,
      refreshToken,
      isAuthenticated: Boolean(user && accessToken),
      completeAuthentication,
      logout,
    }),
    [user, accessToken, refreshToken]
  )

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used inside an AuthProvider')
  }

  return context
}
