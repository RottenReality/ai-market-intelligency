// Indicator values come already worded from the backend (IndicatorResult.display).
const MISSING = 'n/a'

export function formatScore(score: number | null | undefined): string {
  return score === null || score === undefined ? MISSING : String(Math.round(score))
}
