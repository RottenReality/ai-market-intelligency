import { Fragment } from 'react'

// Indicator citations like [A1] or [C1, C3], and numbers that stand alone (so "G1" is not one),
// with an optional minus sign, $, thousands separators, decimals and a %, M or h unit.
const TOKEN =
  /(\[[CAGE]\d(?:\s*,\s*[CAGE]\d)*\])|((?:(?<=^|[\s(])[-−])?(?<![A-Za-z\d.,$])\$?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:%|M\b| h\b)?(?![A-Za-z\d]))/g

/** AI text with its numbers in bold and its indicator citations as small labels. */
export function RichText({ text }: { text: string }) {
  const parts: React.ReactNode[] = []
  let last = 0
  for (const match of text.matchAll(TOKEN)) {
    const start = match.index ?? 0
    // Drop the space before a citation: the label already has its own margin.
    const before = text.slice(last, start)
    parts.push(match[1] ? before.replace(/\s+$/, '') : before)
    if (match[1]) {
      for (const id of match[1].slice(1, -1).split(/\s*,\s*/)) {
        parts.push(
          <span
            key={`${start}-${id}`}
            title={`Indicator ${id}`}
            className="ml-1 inline-block rounded border px-1 align-[1px] text-[10px] leading-4 font-medium text-muted-foreground"
          >
            {id}
          </span>,
        )
      }
    } else {
      parts.push(
        <strong key={start} className="font-semibold text-foreground">
          {match[2]}
        </strong>,
      )
    }
    last = start + match[0].length
  }
  parts.push(text.slice(last))
  return (
    <>
      {parts.map((part, index) => (
        <Fragment key={index}>{part}</Fragment>
      ))}
    </>
  )
}
