import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ApiError } from '@/lib/api'
import { createExplanation, getExplanation } from './api'

function generationError(error: unknown): string {
  if (error instanceof ApiError && error.status === 503) return 'AI is not configured'
  if (error instanceof ApiError && error.status === 502) return 'The AI service failed. Try again.'
  return 'Could not generate the explanation. Try again.'
}

export function ExplanationPanel({ iso3 }: { iso3: string }) {
  const queryClient = useQueryClient()
  const key = ['explanation', iso3]
  const saved = useQuery({ queryKey: key, queryFn: () => getExplanation(iso3) })
  const generate = useMutation({
    mutationFn: () => createExplanation(iso3),
    onSuccess: (explanation) => queryClient.setQueryData(key, explanation),
  })
  const explanation = saved.data

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <CardTitle>AI explanation</CardTitle>
        {saved.isSuccess && !explanation && (
          <Button onClick={() => generate.mutate()} disabled={generate.isPending}>
            Explain
          </Button>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {saved.isPending && <p className="text-sm text-muted-foreground">Loading…</p>}
        {generate.isPending && (
          <p className="text-sm text-muted-foreground">Writing the explanation…</p>
        )}
        {generate.isError && (
          <p role="alert" className="text-sm text-destructive">
            {generationError(generate.error)}
          </p>
        )}
        {saved.isSuccess && !explanation && !generate.isPending && !generate.isError && (
          <p className="text-sm text-muted-foreground">
            Generate a short summary of these results, written by AI from the numbers above.
          </p>
        )}
        {explanation && (
          <>
            {explanation.flagged && (
              <Alert>
                <AlertDescription>
                  Some numbers could not be verified. Review before using.
                </AlertDescription>
              </Alert>
            )}
            <p className="leading-relaxed whitespace-pre-line">{explanation.text}</p>
            <p className="text-xs text-muted-foreground">
              AI-generated from the scores above on {explanation.created_at.slice(0, 10)}. Check it
              before sharing.
            </p>
          </>
        )}
      </CardContent>
    </Card>
  )
}
