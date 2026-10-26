import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ApiStatus } from '@/features/health/ApiStatus'

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <main className="mx-auto max-w-5xl p-6">
        <h1 className="text-2xl font-semibold">CAGE Market Accessibility</h1>
        <ApiStatus />
      </main>
    </QueryClientProvider>
  )
}
