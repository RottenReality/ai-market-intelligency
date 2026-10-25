import { QueryClientProvider } from '@tanstack/react-query'
import { lazy, Suspense } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router'
import { AppShell } from '@/features/auth/AppShell'
import { AuthGate } from '@/features/auth/AuthGate'
import { LoginPage } from '@/features/auth/LoginPage'
import { createQueryClient } from '@/lib/queryClient'

const queryClient = createQueryClient()

// Pages with charts are loaded on demand so the login page stays small.
const ScorecardPage = lazy(() =>
  import('@/features/scorecard/ScorecardPage').then((m) => ({ default: m.ScorecardPage })),
)

function PageLoading() {
  return <p className="text-sm text-muted-foreground">Loading…</p>
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<AuthGate />}>
            <Route element={<AppShell />}>
              <Route
                index
                element={
                  <Suspense fallback={<PageLoading />}>
                    <ScorecardPage />
                  </Suspense>
                }
              />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
