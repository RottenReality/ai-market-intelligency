import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { CountryAnalysis } from '@/lib/types'
import { AnalysisMetaNotes } from './AnalysisMetaNotes'
import { ProviderSelect } from './ProviderSelect'
import { generateCountryAnalysis, getCountryAnalysis } from './api'
import { aiErrorText } from './errors'
import { useProviderChoice } from './useProviderChoice'

const DIMENSIONS = ['Cultural', 'Administrative', 'Geographic', 'Economic'] as const

export function AnalysisPanel({ iso3 }: { iso3: string }) {
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
        {saved.data && <AnalysisContent analysis={saved.data} />}
      </CardContent>
    </Card>
  )
}

function AnalysisContent({ analysis }: { analysis: CountryAnalysis }) {
  const { content } = analysis
  return (
    <div className="flex flex-col gap-4 leading-relaxed">
      <AnalysisMetaNotes meta={analysis} />
      <section className="rounded-md bg-muted p-4">
        <h3 className="mb-1 font-medium">Executive summary</h3>
        <p>{content.executive_summary}</p>
      </section>
      <div className="grid gap-4 md:grid-cols-2">
        {DIMENSIONS.map((dimension) => (
          <section key={dimension}>
            <h3 className="mb-1 font-medium">{dimension}</h3>
            <p className="text-sm">{content.dimensions[dimension]}</p>
          </section>
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <section>
          <h3 className="mb-1 font-medium">Barriers</h3>
          <ul className="list-disc pl-5 text-sm">
            {content.barriers.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </section>
        <section>
          <h3 className="mb-1 font-medium">Opportunities</h3>
          <ul className="list-disc pl-5 text-sm">
            {content.opportunities.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </section>
      </div>
      <section>
        <h3 className="mb-1 font-medium">Recommendation</h3>
        <p className="text-sm">{content.recommendation}</p>
      </section>
    </div>
  )
}
