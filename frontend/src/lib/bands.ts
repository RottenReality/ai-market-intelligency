export type Band = 'barrier' | 'middle' | 'strength'

// Same bands as the PDF heat maps: below 40 is a barrier, 70 and above a strength.
export function bandOf(score: number): Band {
  if (score < 40) return 'barrier'
  if (score < 70) return 'middle'
  return 'strength'
}

export const BAND_STYLES: Record<Band, { chip: string; rule: string }> = {
  barrier: {
    chip: 'bg-red-50 text-red-700 ring-red-200 dark:bg-red-950 dark:text-red-300 dark:ring-red-900',
    rule: 'border-red-400 dark:border-red-700',
  },
  middle: {
    chip: 'bg-amber-50 text-amber-800 ring-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:ring-amber-900',
    rule: 'border-amber-400 dark:border-amber-700',
  },
  strength: {
    chip: 'bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:ring-emerald-900',
    rule: 'border-emerald-500 dark:border-emerald-700',
  },
}
