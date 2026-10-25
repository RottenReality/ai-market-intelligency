// Mirrors the backend API payloads (snake_case kept on purpose: no mapping layer).

export type DimensionId = 'C' | 'A' | 'G' | 'E'
export type RawValue = number | boolean | string | null

export interface Source {
  name: string
  url: string
  year: number | null
}

export interface IndicatorResult {
  id: string
  dimension: DimensionId
  name: string
  status: 'ok' | 'missing'
  score: number | null
  raw: RawValue
  unit: string
  sources: Source[]
}

export interface Dimension {
  id: DimensionId
  name: string
  score: number | null
  available: number
  total: number
}

export interface Scorecard {
  country: { iso3: string; name: string }
  home: string
  indicators: IndicatorResult[]
  dimensions: Dimension[]
  accessibility: number | null
  accessibility_reason: string | null
}

export interface CountrySummary {
  iso3: string
  name: string
  has_data: boolean
}

export interface ComparedCountry {
  iso3: string
  name: string
  has_data: boolean
  accessibility: number | null
  dimensions: Record<DimensionId, number | null>
  indicators_available: number
  indicators_total: number
}

export interface Comparison {
  countries: ComparedCountry[]
}

export interface Explanation {
  iso3: string
  text: string
  flagged: boolean
  created_at: string
}
