import { QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router'
import { AppShell } from '@/features/auth/AppShell'
import { AuthGate } from '@/features/auth/AuthGate'
import { LoginPage } from '@/features/auth/LoginPage'
import { ScorecardPage } from '@/features/scorecard/ScorecardPage'
import { createQueryClient } from '@/lib/queryClient'

const queryClient = createQueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<AuthGate />}>
            <Route element={<AppShell />}>
              <Route index element={<ScorecardPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
