import { Button } from '@/components/ui/button'

/** A plain same-origin link: the browser sends the session cookie and saves the PDF. */
export function ExportPdfButton({ iso3 }: { iso3: string[] }) {
  const href = `/api/reports/pdf?${new URLSearchParams({ iso3: iso3.join(',') })}`
  return (
    <Button asChild variant="outline">
      <a href={href} download>
        Export PDF
      </a>
    </Button>
  )
}
