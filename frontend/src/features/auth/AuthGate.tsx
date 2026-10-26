import { useQuery } from '@tanstack/react-query'
import { Navigate, Outlet } from 'react-router'
import { ME_KEY } from '@/lib/queryClient'
import { getMe } from './api'

export function AuthGate() {
  const { data, isPending, isError } = useQuery({ queryKey: ME_KEY, queryFn: getMe })

  if (isPending) return <p className="p-6 text-sm text-muted-foreground">Loading…</p>
  if (isError || !data) return <Navigate to="/login" replace />
  return <Outlet context={data} />
}
