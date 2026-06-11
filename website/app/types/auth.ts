export interface ApiResponse<T = unknown> {
  status: boolean
  data: T | null
  message: string | null
  errors: Record<string, unknown> | null
  timestamp: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number // seconds
}

export interface User {
  id: number
  username: string
  email: string
  created_at: string
}

export interface LoginPayload {
  username: string
  password: string
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
}
