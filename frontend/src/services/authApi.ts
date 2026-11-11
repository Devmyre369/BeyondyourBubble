
import api from './api'

export interface SignupData {
  username: string
  email: string
  password: string
  confirm_password: string
}

export interface AuthUser {
  id: string
  username: string
  email: string
  email_verified: boolean
}

export interface AuthResponse {
  success: boolean
  message: string
  user: AuthUser
  tokens: {
    access: string
    refresh: string
  }
}

export interface MessageResponse {
  success: boolean
  message: string
  email?: string
}

export const authApi = {
  signup: async (data: SignupData) => {
    const response = await api.post<MessageResponse>(
      '/accounts/signup/',
      data
    )
    return response.data
  },

  verifySignup: async (email: string, otp: string) => {
    const response = await api.post<AuthResponse>(
      '/accounts/verify-signup/',
      { email, otp }
    )
    return response.data
  },

  login: async (username: string, password: string) => {
    const response = await api.post<AuthResponse>(
      '/accounts/login/',
      { username, password }
    )
    return response.data
  },

  requestPasswordReset: async (email: string) => {
    const response = await api.post<MessageResponse>(
      '/accounts/password-reset/',
      { email }
    )
    return response.data
  },

  confirmPasswordReset: async (
    email: string,
    otp: string,
    new_password: string,
    confirm_password: string
  ) => {
    const response = await api.post<MessageResponse>(
      '/accounts/password-reset/confirm/',
      {
        email,
        otp,
        new_password,
        confirm_password,
      }
    )
    return response.data
  },

  refreshToken: async (refresh: string) => {
    const response = await api.post<{ access: string; refresh?: string }>(
      '/accounts/token/refresh/',
      { refresh }
    )
    return response.data
  },
}

export default authApi
