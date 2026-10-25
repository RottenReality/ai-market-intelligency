import { useQuery } from '@tanstack/react-query'
import { getHealth } from './api'

export function ApiStatus() {
  const { isPending, isError } = useQuery({ queryKey: ['health'], queryFn: getHealth })

  if (isPending) return <span className="text-sm text-muted-foreground">Checking API…</span>
  if (isError) return <span className="text-sm text-destructive">API unreachable</span>
  return <span className="text-sm text-muted-foreground">API connected</span>
}
