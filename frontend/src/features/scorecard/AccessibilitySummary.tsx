import { Card, CardContent } from '@/components/ui/card'
import type { Scorecard } from '@/lib/types'

export function AccessibilitySummary({ scorecard }: { scorecard: Scorecard }) {
  const { accessibility, accessibility_reason: reason } = scorecard
  return (
    <Card>
      <CardContent className="flex flex-col gap-1">
        <span className="text-sm text-muted-foreground">Market accessibility</span>
        {accessibility === null ? (
          <p className="text-base font-medium">{reason}</p>
        ) : (
          <span className="text-4xl font-semibold tabular-nums">
            {Math.round(accessibility)}%
          </span>
        )}
        <span className="text-xs text-muted-foreground">
          {scorecard.country.name} compared with {scorecard.home} · CAGE model, equal weights
        </span>
      </CardContent>
    </Card>
  )
}
