import { apiFetch } from '@/lib/api'
import type { Profile, ProfileEdits } from '@/lib/types'

export function getProfile(): Promise<Profile> {
  return apiFetch('/api/profile')
}

export function saveProfile(edits: ProfileEdits): Promise<Profile> {
  return apiFetch('/api/profile', { method: 'PUT', body: JSON.stringify(edits) })
}

export function resetProfile(): Promise<Profile> {
  return apiFetch('/api/profile', { method: 'DELETE' })
}
