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
  /** Short value for tables, e.g. "English: Low" or "3 h difference". */
  display: string
  /** One plain sentence: what the value is, its scale and its direction. */
  meaning: string | null
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

export interface ProviderInfo {
  id: string
  label: string
  model: string
}

export interface CountryAnalysisContent {
  executive_summary: string
  dimensions: Record<'Cultural' | 'Administrative' | 'Geographic' | 'Economic', string>
  barriers: string[]
  opportunities: string[]
  recommendation: string
}

export interface AnalysisMeta {
  provider: string
  provider_label: string
  model: string
  created_at: string
  flagged: boolean
  /** A share of users was still described as a preference after the retry. */
  overstated: boolean
  outdated: boolean
}

export interface CountryAnalysis extends AnalysisMeta {
  iso3: string
  content: CountryAnalysisContent
}

export interface ProfileEdits {
  name: string
  description: string
  supported_languages: string[]
  channels: string[]
}

export interface Profile extends ProfileEdits {
  home_country: string
  home_timezone: string
  source: 'saved' | 'file'
  options: { languages: string[]; channels: string[] }
}

export interface RankedExplanation {
  iso3: string
  name: string
  accessibility: number | null
  rank: number
  explanation: string
}

export interface ComparisonInsight extends AnalysisMeta {
  countries: string[]
  summary: string
  ranking: RankedExplanation[]
  key_differences: string[]
}
