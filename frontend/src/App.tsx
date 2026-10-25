import { QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router'
import { AppShell } from '@/features/auth/AppShell'
import { AuthGate } from '@/features/auth/AuthGate'
import { LoginPage } from '@/features/auth/LoginPage'
import { createQueryClient } from '@/lib/queryClient'

const queryClient = createQueryClient()

function Home() {
  return <p className="text-muted-foreground">Country scorecards will appear here.</p>
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<AuthGate />}>
            <Route element={<AppShell />}>
              <Route index element={<Home />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
