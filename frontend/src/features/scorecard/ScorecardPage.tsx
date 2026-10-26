import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import { ExplanationPanel } from '@/features/explanation/ExplanationPanel'
import { ExportPdfButton } from '@/features/report/ExportPdfButton'
import { ApiError } from '@/lib/api'
import type { Scorecard } from '@/lib/types'
import { AccessibilitySummary } from './AccessibilitySummary'
import { CountryPicker } from './CountryPicker'
import { DimensionRadar } from './DimensionRadar'
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
        <div className="flex flex-wrap items-center gap-3">
          {countries.data && (
            <CountryPicker
              countries={countries.data}
              value={iso3}
              onChange={(code) => setParams({ country: code })}
            />
          )}
          {scorecard.data && <ExportPdfButton iso3={[scorecard.data.country.iso3]} />}
        </div>
      </div>

      {iso3 === '' && (
        <p className="text-muted-foreground">Select a country to see its CAGE indicators.</p>
      )}
      {scorecard.isError && (
        <p role="alert" className="text-destructive">
          {scorecardError(scorecard.error)}
        </p>
      )}
      {scorecard.data && <ScorecardView scorecard={scorecard.data} />}
    </section>
  )
}

function ScorecardView({ scorecard }: { scorecard: Scorecard }) {
  return (
    <div className="flex flex-col gap-6">
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_auto]">
        <AccessibilitySummary scorecard={scorecard} />
        <DimensionRadar dimensions={scorecard.dimensions} />
      </div>
      <ExplanationPanel iso3={scorecard.country.iso3} />
      {scorecard.dimensions.map((dimension) => (
        <section
          key={dimension.id}
          aria-label={`${dimension.name} indicators`}
          className="flex flex-col gap-2"
        >
          <h2 className="text-lg font-medium">{dimension.name}</h2>
          <IndicatorTable
            indicators={scorecard.indicators.filter((i) => i.dimension === dimension.id)}
          />
        </section>
      ))}
    </div>
  )
}
