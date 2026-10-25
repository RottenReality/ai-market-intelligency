import { apiFetch } from '@/lib/api'
import type { Comparison } from '@/lib/types'

export function getComparison(iso3: string[]): Promise<Comparison> {
  const params = new URLSearchParams({ iso3: iso3.join(',') })
  return apiFetch(`/api/comparison?${params}`)
}
