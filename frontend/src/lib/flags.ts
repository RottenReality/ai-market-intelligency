import { ISO2 } from './iso2'

// Regional indicator letters: two of them in a row render as the country's flag.
const REGIONAL_A = 0x1f1e6

/** The flag emoji for an ISO3 code ("COL" -> 🇨🇴), or "" when the code is unknown. */
export function flagEmoji(iso3: string): string {
  const iso2 = ISO2[iso3.toUpperCase()]
  if (!iso2) return ''
  return String.fromCodePoint(...[...iso2].map((letter) => REGIONAL_A + letter.charCodeAt(0) - 65))
}
