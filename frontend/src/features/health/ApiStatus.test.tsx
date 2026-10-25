import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { ApiStatus } from './ApiStatus'
import { getHealth } from './api'

vi.mock('./api')

function renderStatus() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <ApiStatus />
    </QueryClientProvider>,
  )
}

test('shows "API connected" when health returns ok', async () => {
  vi.mocked(getHealth).mockResolvedValue({ status: 'ok' })
  renderStatus()
  expect(await screen.findByText('API connected')).toBeInTheDocument()
})

test('shows "API unreachable" when the request fails', async () => {
  vi.mocked(getHealth).mockRejectedValue(new Error('network down'))
  renderStatus()
  expect(await screen.findByText('API unreachable')).toBeInTheDocument()
})
