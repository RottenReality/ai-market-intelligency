import type { RawValue } from './types'

const MISSING = 'n/a'
const usd = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })

function formatBand(value: string): string {
  const text = value.replace(/_/g, ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

export function formatRaw(value: RawValue | undefined, unit: string): string {
  if (value === null || value === undefined) return MISSING
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'string') return formatBand(value)
  switch (unit) {
    case '%':
      return `${value.toFixed(1)}%`
    case 'USD':
      return `$${usd.format(value)}`
    case 'people':
      return value >= 1_000_000 ? `${(value / 1_000_000).toFixed(1)}M` : usd.format(value)
    case 'index':
      return value.toFixed(2)
    case 'hours':
      return `${value} h`
    default:
      return String(Math.round(value * 100) / 100)
  }
}

export function formatScore(score: number | null | undefined): string {
  return score === null || score === undefined ? MISSING : String(Math.round(score))
}
