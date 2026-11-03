import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { ComparisonInsight } from '@/lib/types'
import { AnalysisMetaNotes } from './AnalysisMetaNotes'
import { ProviderSelect } from './ProviderSelect'
import { RichText } from './RichText'
import { ScoreChip } from './ScoreChip'
import { generateComparisonInsight, getComparisonInsight } from './api'
import { aiErrorText } from './errors'
import { useProviderChoice } from './useProviderChoice'

/** AI explanation of why the selected countries (those with data) rank as they do. */
export function ComparisonInsightPanel({ codes }: { codes: string[] }) {
  const queryClient = useQueryClient()
  const enough = codes.length >= 2
  const key = ['insight', [...codes].sort().join(',')]
  const saved = useQuery({
    queryKey: key,
    queryFn: () => getComparisonInsight(codes),
    enabled: enough,
  })
  const { providers, list, selected, choose } = useProviderChoice()
  const generate = useMutation({
    mutationFn: () => generateComparisonInsight(codes, selected),
    onSuccess: (insight) => queryClient.setQueryData(key, insight),
  })

  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
        <CardTitle>Comparison insight</CardTitle>
        {enough && list.length > 0 && (
          <div className="flex flex-wrap items-center gap-3">
            <ProviderSelect providers={list} value={selected} onChange={choose} />
            <Button onClick={() => generate.mutate()} disabled={generate.isPending}>
              Generate
            </Button>
          </div>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {!enough && (
          <p className="text-sm text-muted-foreground">
            Select at least two countries with data to compare them with AI.
          </p>
        )}
        {enough && providers.isSuccess && list.length === 0 && (
          <p className="text-sm text-muted-foreground">AI is not configured</p>
        )}
        {generate.isPending && (
          <p className="text-sm text-muted-foreground">Writing the insight… this can take up to two minutes.</p>
        )}
        {generate.isError && (
          <p role="alert" className="text-sm text-destructive">
            {aiErrorText(generate.error)}
          </p>
        )}
        {enough && saved.data && <InsightContent insight={saved.data} />}
      </CardContent>
    </Card>
  )
}

function InsightContent({ insight }: { insight: ComparisonInsight }) {
  return (
    <div className="flex flex-col gap-6">
      <AnalysisMetaNotes meta={insight} />
      <section className="rounded-lg border-l-4 border-[#2a78d6] bg-[#eef4fc] px-5 py-4 dark:bg-[#13233a]">
        <h3 className="mb-2 font-semibold">Summary</h3>
        <p className="leading-7">
          <RichText text={insight.summary} />
        </p>
      </section>
      <section>
        <h3 className="mb-3 font-semibold">Why they rank this way</h3>
        <ol aria-label="Ranking" className="flex flex-col gap-4">
          {insight.ranking.map((entry) => (
            <li key={entry.iso3} className="flex gap-3">
              <span
                aria-hidden
                className="flex size-7 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold tabular-nums"
              >
                {entry.rank}
              </span>
              <div className="flex flex-col gap-1">
                <p className="flex items-center gap-2 font-medium">
                  <span className="sr-only">{entry.rank}. </span>
                  {entry.name}
                  {entry.accessibility === null ? (
                    <span className="text-sm text-muted-foreground">not calculated</span>
                  ) : (
                    <ScoreChip score={entry.accessibility} suffix="%" />
                  )}
                </p>
                <p className="text-sm leading-6">
                  <RichText text={entry.explanation} />
                </p>
              </div>
            </li>
          ))}
        </ol>
      </section>
      <section>
        <h3 className="mb-2 font-semibold">Key differences</h3>
        <ul className="flex list-disc flex-col gap-1.5 pl-5 text-sm leading-6 marker:text-muted-foreground">
          {insight.key_differences.map((item) => (
            <li key={item}>
              <RichText text={item} />
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
