import { ApiError, apiFetch } from '@/lib/api'
import type { Explanation } from '@/lib/types'

const url = (iso3: string) => `/api/countries/${encodeURIComponent(iso3)}/explanation`

/** The saved explanation for the current data, or null when none has been generated yet. */
export async function getExplanation(iso3: string): Promise<Explanation | null> {
  try {
    return await apiFetch<Explanation>(url(iso3))
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null
    throw error
  }
}

export function createExplanation(iso3: string): Promise<Explanation> {
  return apiFetch(url(iso3), { method: 'POST' })
}
