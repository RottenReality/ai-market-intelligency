import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BAND_STYLES, bandOf } from '@/lib/bands'
import { splitSentences } from '@/lib/sentences'
import type { CountryAnalysis, Dimension } from '@/lib/types'
import { cn } from '@/lib/utils'
import { AnalysisMetaNotes } from './AnalysisMetaNotes'
import { ProviderSelect } from './ProviderSelect'
import { RichText } from './RichText'
import { ScoreChip } from './ScoreChip'
import { generateCountryAnalysis, getCountryAnalysis } from './api'
import { aiErrorText } from './errors'
import { useProviderChoice } from './useProviderChoice'

const DIMENSIONS = ['Cultural', 'Administrative', 'Geographic', 'Economic'] as const

/** `dimensions` (from the scorecard) adds each dimension's score next to its explanation. */
export function AnalysisPanel({ iso3, dimensions }: { iso3: string; dimensions?: Dimension[] }) {
  const queryClient = useQueryClient()
  const key = ['analysis', iso3]
  const saved = useQuery({ queryKey: key, queryFn: () => getCountryAnalysis(iso3) })
  const { providers, list, selected, choose } = useProviderChoice()
  const generate = useMutation({
    mutationFn: () => generateCountryAnalysis(iso3, selected),
    onSuccess: (analysis) => queryClient.setQueryData(key, analysis),
  })

  const noProviders = providers.isSuccess && list.length === 0

  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
        <CardTitle>AI analysis</CardTitle>
        {list.length > 0 && (
          <div className="flex flex-wrap items-center gap-3">
            <ProviderSelect providers={list} value={selected} onChange={choose} />
            <Button onClick={() => generate.mutate()} disabled={generate.isPending}>
              Generate
            </Button>
          </div>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {noProviders && <p className="text-sm text-muted-foreground">AI is not configured</p>}
        {generate.isPending && (
          <p className="text-sm text-muted-foreground">Writing the analysis… this can take up to two minutes.</p>
        )}
        {generate.isError && (
          <p role="alert" className="text-sm text-destructive">
            {aiErrorText(generate.error)}
          </p>
        )}
        {saved.isSuccess && !saved.data && !generate.isPending && !noProviders && (
          <p className="text-sm text-muted-foreground">
            Choose an AI and click Generate for a written analysis of these results: why each
            dimension scored as it did, the main barriers and opportunities, and next steps.
          </p>
        )}
        {saved.data && <AnalysisContent analysis={saved.data} dimensions={dimensions} />}
      </CardContent>
    </Card>
  )
}

function AnalysisContent({
  analysis,
  dimensions,
}: {
  analysis: CountryAnalysis
  dimensions?: Dimension[]
}) {
  const { content } = analysis
  const scores = new Map(dimensions?.map((d) => [d.name, d.score]))
  return (
    <div className="flex flex-col gap-6">
      <AnalysisMetaNotes meta={analysis} />

      <section className="rounded-lg border-l-4 border-[#2a78d6] bg-[#eef4fc] px-5 py-4 dark:bg-[#13233a]">
        <h3 className="mb-2 font-semibold">Executive summary</h3>
        <p className="leading-7">
          <RichText text={content.executive_summary} />
        </p>
      </section>

      <div>
        <h3 className="mb-3 font-semibold">Why each dimension scored this way</h3>
        <div className="grid gap-x-6 gap-y-5 md:grid-cols-2">
          {DIMENSIONS.map((dimension) => {
            const score = scores.get(dimension)
            const band = score === null || score === undefined ? null : bandOf(score)
            return (
              <section
                key={dimension}
                className={cn('border-l-2 pl-4', band ? BAND_STYLES[band].rule : 'border-border')}
              >
                <h4 className="mb-1.5 flex items-center gap-2 font-medium">
                  {dimension}
                  {score !== null && score !== undefined && <ScoreChip score={score} />}
                </h4>
                <Points text={content.dimensions[dimension]} />
              </section>
            )
          })}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <MarkedList title="Barriers" items={content.barriers} marker="bg-red-500" />
        <MarkedList title="Opportunities" items={content.opportunities} marker="bg-emerald-500" />
      </div>

      <section className="rounded-lg bg-muted/60 px-5 py-4">
        <h3 className="mb-2 font-semibold">Recommendation and next steps</h3>
        <Points text={content.recommendation} />
      </section>
    </div>
  )
}

/** One bullet per sentence, so long paragraphs read as separate points. */
function Points({ text }: { text: string }) {
  return (
    <ul className="flex list-disc flex-col gap-1.5 pl-5 text-sm leading-6 marker:text-muted-foreground">
      {splitSentences(text).map((sentence, index) => (
        <li key={index}>
          <RichText text={sentence} />
        </li>
      ))}
    </ul>
  )
}

function MarkedList({ title, items, marker }: { title: string; items: string[]; marker: string }) {
  return (
    <section>
      <h3 className="mb-2 flex items-center gap-2 font-semibold">
        <span aria-hidden className={cn('size-2 rounded-full', marker)} />
        {title}
      </h3>
      <ul className="flex flex-col gap-2 text-sm leading-6">
        {items.map((item) => (
          <li key={item} className="flex gap-2">
            <span aria-hidden className={cn('mt-2.5 size-1.5 shrink-0 rounded-full', marker)} />
            <span>
              <RichText text={item} />
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}
