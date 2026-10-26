import { apiFetch } from '@/lib/api'
import type { CountrySummary, Scorecard } from '@/lib/types'

export function getCountries(): Promise<CountrySummary[]> {
  return apiFetch('/api/countries')
}

export function getScorecard(iso3: string): Promise<Scorecard> {
  return apiFetch(`/api/countries/${encodeURIComponent(iso3)}/scorecard`)
}
