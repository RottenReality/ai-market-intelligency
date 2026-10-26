import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Outlet, useNavigate, useOutletContext } from 'react-router'
import { Button } from '@/components/ui/button'
import { ApiStatus } from '@/features/health/ApiStatus'
import { ME_KEY } from '@/lib/queryClient'
import { logout } from './api'

export function AppShell() {
  const user = useOutletContext<{ username: string }>()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const signOut = useMutation({
    mutationFn: logout,
    onSettled: () => {
      queryClient.setQueryData(ME_KEY, null)
      navigate('/login', { replace: true })
    },
  })

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-3">
          <span className="font-semibold">CAGE Market Accessibility</span>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-muted-foreground">{user.username}</span>
            <Button variant="outline" size="sm" onClick={() => signOut.mutate()}>
              Log out
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-6">
        <Outlet />
      </main>
      <footer className="mx-auto w-full max-w-6xl px-6 py-3">
        <ApiStatus />
      </footer>
    </div>
  )
}
