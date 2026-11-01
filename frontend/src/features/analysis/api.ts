import { ApiError, apiFetch } from '@/lib/api'
import type { CountryAnalysis, ProviderInfo } from '@/lib/types'

const analysisUrl = (iso3: string) => `/api/countries/${encodeURIComponent(iso3)}/analysis`

export function getProviders(): Promise<ProviderInfo[]> {
  return apiFetch('/api/ai/providers')
}

/** The saved analysis for a country, or null when none has been generated yet. */
export async function getCountryAnalysis(iso3: string): Promise<CountryAnalysis | null> {
  try {
    return await apiFetch<CountryAnalysis>(analysisUrl(iso3))
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null
    throw error
  }
}

export function generateCountryAnalysis(iso3: string, provider: string): Promise<CountryAnalysis> {
  return apiFetch(analysisUrl(iso3), { method: 'POST', body: JSON.stringify({ provider }) })
}
