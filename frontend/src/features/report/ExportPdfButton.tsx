import { Button } from '@/components/ui/button'

function missingNote(missing: number, total: number): string | null {
  if (missing <= 0) return null
  if (total === 1) return 'This country has no AI analysis yet'
  return `${missing} of ${total} countries have no AI analysis yet`
}

/** A plain same-origin link: the browser sends the session cookie and saves the PDF. */
export function ExportPdfButton({ iso3, missingAnalyses }: { iso3: string[]; missingAnalyses: number }) {
  const href = `/api/reports/pdf?${new URLSearchParams({ iso3: iso3.join(',') })}`
  const note = missingNote(missingAnalyses, iso3.length)
  return (
    <div className="flex flex-col items-end gap-1">
      <Button asChild variant="outline">
        <a href={href} download>
          Export PDF
        </a>
      </Button>
      {note && <p className="text-xs text-muted-foreground">{note}</p>}
    </div>
  )
}
