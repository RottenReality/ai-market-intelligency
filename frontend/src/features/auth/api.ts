import { apiFetch } from '@/lib/api'

export function login(username: string, password: string): Promise<void> {
  return apiFetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export function logout(): Promise<void> {
  return apiFetch('/api/auth/logout', { method: 'POST' })
}

export function getMe(): Promise<{ username: string }> {
  return apiFetch('/api/auth/me')
}
