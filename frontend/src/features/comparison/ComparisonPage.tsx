import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { getCountries } from '@/features/scorecard/api'
import { ApiError } from '@/lib/api'
import { MAX_RADAR_SERIES } from '@/lib/colors'
import { formatScore } from '@/lib/format'
import type { ComparedCountry, DimensionId } from '@/lib/types'
import { RadarOverlay } from './RadarOverlay'
import { RankingChart } from './RankingChart'
import { getComparison } from './api'

const DIMENSION_COLUMNS: [DimensionId, string][] = [
  ['C', 'Cultural'],
  ['A', 'Administrative'],
  ['G', 'Geographic'],
  ['E', 'Economic'],
]

function parseSelection(value: string | null): string[] {
  return (value ?? '').split(',').filter(Boolean)
}

export function ComparisonPage() {
  const [params, setParams] = useSearchParams()
  const selected = parseSelection(params.get('iso3'))
  const countries = useQuery({ queryKey: ['countries'], queryFn: getCountries })
  const comparison = useQuery({
    queryKey: ['comparison', selected],
    queryFn: () => getComparison(selected),
    enabled: selected.length > 0,
  })

  function toggle(iso3: string) {
    const next = selected.includes(iso3)
      ? selected.filter((code) => code !== iso3)
      : [...selected, iso3]
    setParams(next.length ? { iso3: next.join(',') } : {})
  }

  return (
    <section className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">Compare countries</h1>

      <fieldset className="flex flex-wrap gap-x-6 gap-y-2">
        <legend className="mb-2 text-sm font-medium">Countries</legend>
        {countries.data?.map((country) => (
          <label key={country.iso3} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              className="size-4 accent-primary"
              checked={selected.includes(country.iso3)}
              onChange={() => toggle(country.iso3)}
            />
            {country.name}
          </label>
        ))}
      </fieldset>

      {selected.length === 0 && (
        <p className="text-muted-foreground">Select countries to compare.</p>
      )}
      {comparison.isError && (
        <p role="alert" className="text-destructive">
          {comparison.error instanceof ApiError
            ? comparison.error.detail
            : 'Could not load the comparison. Please try again.'}
        </p>
      )}
      {comparison.data && <ComparisonView countries={comparison.data.countries} />}
    </section>
  )
}

function ComparisonView({ countries }: { countries: ComparedCountry[] }) {
  const withScore = countries.filter((c) => c.accessibility !== null)
  const coverage = new Set(countries.map((c) => c.indicators_available))
  return (
    <div className="flex flex-col gap-6">
      {coverage.size > 1 && (
        <p role="note" className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
          Countries have different amounts of data. Missing indicators are left out of the
          averages, so compare with care.
        </p>
      )}
      <div className="flex flex-wrap items-start gap-8">
        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">Market accessibility ranking</h2>
          <RankingChart countries={countries} />
        </div>
        {withScore.length > 0 && (
          <div className="flex flex-col gap-2">
            <h2 className="text-lg font-medium">CAGE profile</h2>
            <RadarOverlay countries={withScore} />
            {withScore.length > MAX_RADAR_SERIES && (
              <p className="text-sm text-muted-foreground">
                The radar shows the first {MAX_RADAR_SERIES} countries in the ranking.
              </p>
            )}
          </div>
        )}
      </div>

      <Table aria-label="Comparison values">
        <TableCaption>Scores from 0 (hard to access) to 100 (very accessible).</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Country</TableHead>
            <TableHead className="text-right">Accessibility</TableHead>
            {DIMENSION_COLUMNS.map(([id, name]) => (
              <TableHead key={id} className="text-right">
                {name}
              </TableHead>
            ))}
            <TableHead className="text-right">Data</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {countries.map((country) => (
            <TableRow key={country.iso3}>
              <TableCell className="font-medium">{country.name}</TableCell>
              <TableCell className="text-right tabular-nums">
                {country.has_data
                  ? country.accessibility === null
                    ? 'not enough data'
                    : `${Math.round(country.accessibility)}%`
                  : 'no data'}
              </TableCell>
              {DIMENSION_COLUMNS.map(([id]) => (
                <TableCell key={id} className="text-right tabular-nums">
                  {formatScore(country.dimensions[id])}
                </TableCell>
              ))}
              <TableCell className="text-right text-muted-foreground tabular-nums">
                {country.indicators_available}/{country.indicators_total}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
