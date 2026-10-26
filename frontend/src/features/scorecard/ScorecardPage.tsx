import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import { ApiError } from '@/lib/api'
import { CountryPicker } from './CountryPicker'
import { IndicatorTable } from './IndicatorTable'
import { getCountries, getScorecard } from './api'

function scorecardError(error: unknown): string {
  if (error instanceof ApiError && (error.status === 404 || error.status === 409)) {
    return error.detail
  }
  return 'Could not load the scorecard. Please try again.'
}

export function ScorecardPage() {
  const [params, setParams] = useSearchParams()
  const iso3 = params.get('country') ?? ''
  const countries = useQuery({ queryKey: ['countries'], queryFn: getCountries })
  const scorecard = useQuery({
    queryKey: ['scorecard', iso3],
    queryFn: () => getScorecard(iso3),
    enabled: iso3 !== '',
  })

  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-xl font-semibold">Country scorecard</h1>
        {countries.data && (
          <CountryPicker
            countries={countries.data}
            value={iso3}
            onChange={(code) => setParams({ country: code })}
          />
        )}
      </div>

      {iso3 === '' && (
        <p className="text-muted-foreground">Select a country to see its CAGE indicators.</p>
      )}
      {scorecard.isError && (
        <p role="alert" className="text-destructive">
          {scorecardError(scorecard.error)}
        </p>
      )}
      {scorecard.data && <IndicatorTable indicators={scorecard.data.indicators} />}
    </section>
  )
}
