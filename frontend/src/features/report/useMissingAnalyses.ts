import { useQueries } from '@tanstack/react-query'
import { getCountryAnalysis } from '@/features/analysis/api'

/**
 * How many of these countries have no saved AI analysis. Shares the ['analysis', iso3] cache
 * with the analysis panel, so generating one updates the count. Outdated counts as present.
 */
export function useMissingAnalyses(iso3: string[]): number {
  const results = useQueries({
    queries: iso3.map((code) => ({
      queryKey: ['analysis', code],
      queryFn: () => getCountryAnalysis(code),
    })),
  })
  return results.filter((result) => result.isSuccess && result.data === null).length
}
