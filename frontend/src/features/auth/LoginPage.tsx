import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError } from '@/lib/api'
import { ME_KEY } from '@/lib/queryClient'
import { getMe, login } from './api'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError && (error.status === 401 || error.status === 429)) {
    return error.detail
  }
  return 'Could not sign in. Please try again.'
}

export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const signIn = useMutation({
    mutationFn: () => login(username, password),
    onSuccess: async () => {
      // Load the user before navigating: a cached "no user" from the earlier 401
      // would otherwise make AuthGate bounce straight back to /login.
      await queryClient.fetchQuery({ queryKey: ME_KEY, queryFn: getMe, staleTime: 0 })
      navigate('/', { replace: true })
    },
  })

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    signIn.mutate()
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>CAGE Market Accessibility</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-4" onSubmit={onSubmit}>
            <div className="flex flex-col gap-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {signIn.isError && (
              <p role="alert" className="text-sm text-destructive">
                {errorMessage(signIn.error)}
              </p>
            )}
            <Button type="submit" disabled={signIn.isPending}>
              Sign in
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
