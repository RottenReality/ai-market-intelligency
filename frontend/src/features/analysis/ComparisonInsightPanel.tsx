import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { ComparisonInsight } from '@/lib/types'
import { AnalysisMetaNotes } from './AnalysisMetaNotes'
import { ProviderSelect } from './ProviderSelect'
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
    <div className="flex flex-col gap-4 leading-relaxed">
      <AnalysisMetaNotes meta={insight} />
      <p className="rounded-md bg-muted p-4">{insight.summary}</p>
      <section>
        <h3 className="mb-2 font-medium">Why they rank this way</h3>
        <ol aria-label="Ranking" className="flex flex-col gap-2">
          {insight.ranking.map((entry) => (
            <li key={entry.iso3} className="text-sm">
              <b>
                {entry.rank}. {entry.name}
              </b>{' '}
              <span className="text-muted-foreground tabular-nums">
                {entry.accessibility === null ? 'not calculated' : `${Math.round(entry.accessibility)}%`}
              </span>
              {' · '}
              {entry.explanation}
            </li>
          ))}
        </ol>
      </section>
      <section>
        <h3 className="mb-1 font-medium">Key differences</h3>
        <ul className="list-disc pl-5 text-sm">
          {insight.key_differences.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </section>
    </div>
  )
}
