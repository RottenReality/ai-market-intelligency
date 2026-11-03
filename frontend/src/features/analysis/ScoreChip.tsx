import { BAND_STYLES, bandOf } from '@/lib/bands'
import { cn } from '@/lib/utils'

/** A 0-100 score, coloured by band; the number is always printed, so colour is never the only cue. */
export function ScoreChip({ score, suffix = '' }: { score: number; suffix?: string }) {
  const rounded = Math.round(score)
  const band = bandOf(score)
  return (
    <span
      aria-label={`Score ${rounded} of 100`}
      data-band={band}
      className={cn(
        'inline-flex min-w-8 justify-center rounded-md px-1.5 py-0.5 text-xs font-semibold tabular-nums ring-1 ring-inset',
        BAND_STYLES[band].chip,
      )}
    >
      {rounded}
      {suffix}
    </span>
  )
}
