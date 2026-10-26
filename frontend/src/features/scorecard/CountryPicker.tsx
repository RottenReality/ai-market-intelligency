import type { CountrySummary } from '@/lib/types'

interface Props {
  countries: CountrySummary[]
  value: string
  onChange: (iso3: string) => void
}

export function CountryPicker({ countries, value, onChange }: Props) {
  return (
    <div className="flex items-center gap-3">
      <label htmlFor="country" className="text-sm font-medium">
        Country
      </label>
      <select
        id="country"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-xs focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
      >
        <option value="" disabled>
          Select a country
        </option>
        {countries.map((country) => (
          <option key={country.iso3} value={country.iso3}>
            {country.name}
            {country.has_data ? '' : ' (no data yet)'}
          </option>
        ))}
      </select>
    </div>
  )
}
