import { ApiError, apiFetch } from '@/lib/api'
import type { ComparisonInsight, CountryAnalysis, ProviderInfo } from '@/lib/types'

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

/** The saved insight for exactly these countries (any order), or null. */
export async function getComparisonInsight(codes: string[]): Promise<ComparisonInsight | null> {
  const params = new URLSearchParams({ iso3: codes.join(',') })
  try {
    return await apiFetch<ComparisonInsight>(`/api/comparison/insight?${params}`)
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null
    throw error
  }
}

export function generateComparisonInsight(
  codes: string[],
  provider: string,
): Promise<ComparisonInsight> {
  return apiFetch('/api/comparison/insight', {
    method: 'POST',
    body: JSON.stringify({ iso3: codes, provider }),
  })
}
