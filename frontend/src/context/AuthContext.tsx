
import { createContext, useContext } from 'react'

import type { AuthResponse, AuthUser } from '../services/authApi'
import type { UserProfile } from '../services/profileApi'

export interface AuthContextType {
  user: AuthUser | null
  profile: UserProfile | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  profileLoaded: boolean
  completeAuthentication: (data: AuthResponse) => void
  setProfile: (profile: UserProfile | null) => void
  logout: () => void
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used inside an AuthProvider')
  }

  return context
}
