import { Alert, AlertDescription } from '@/components/ui/alert'
import type { AnalysisMeta } from '@/lib/types'

export function AnalysisMetaNotes({ meta }: { meta: AnalysisMeta }) {
  return (
    <div className="flex flex-col gap-2">
      {meta.outdated && (
        <Alert>
          <AlertDescription>
            Written before the latest data or company change. Generate again to update.
          </AlertDescription>
        </Alert>
      )}
      {meta.flagged && (
        <Alert>
          <AlertDescription>Some numbers could not be verified; review before use.</AlertDescription>
        </Alert>
      )}
      <p className="text-xs text-muted-foreground">
        Written by {meta.provider_label} ({meta.model}) on {meta.created_at.slice(0, 10)}
      </p>
    </div>
  )
}
