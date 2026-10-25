import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { ApiError } from '@/lib/api'
import { createQueryClient } from '@/lib/queryClient'
import type { Scorecard } from '@/lib/types'
import { ScorecardPage } from './ScorecardPage'
import { getCountries, getScorecard } from './api'

vi.mock('./api')

const colombia: Scorecard = {
  country: { iso3: 'COL', name: 'Colombia' },
  home: 'USA',
  indicators: [
    {
      id: 'A3', dimension: 'A', name: 'Regulatory quality', status: 'ok', score: 46.05,
      raw: -0.1973526, unit: 'index',
      sources: [{ name: 'World Bank', url: 'https://api.worldbank.org/a3', year: 2025 }],
    },
    {
      id: 'E3', dimension: 'E', name: 'Inflation', status: 'missing', score: null, raw: null,
      unit: '%', sources: [],
    },
  ],
}

function renderPage(path = '/') {
  render(
    <QueryClientProvider client={createQueryClient()}>
      <MemoryRouter initialEntries={[path]}>
        <ScorecardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(getCountries).mockResolvedValue([
    { iso3: 'COL', name: 'Colombia', has_data: true },
    { iso3: 'MEX', name: 'Mexico', has_data: false },
  ])
  vi.mocked(getScorecard).mockReset()
})

test('choosing a country shows its indicators', async () => {
  vi.mocked(getScorecard).mockResolvedValue(colombia)
  renderPage()
  await userEvent.selectOptions(await screen.findByLabelText('Country'), 'COL')
  const row = (await screen.findByText('Regulatory quality')).closest('tr')!
  expect(within(row).getByText('46')).toBeInTheDocument()
  expect(within(row).getByText('-0.20')).toBeInTheDocument()
  expect(getScorecard).toHaveBeenCalledWith('COL')
})

test('missing indicator shows n/a', async () => {
  vi.mocked(getScorecard).mockResolvedValue(colombia)
  renderPage('/?country=COL')
  const row = (await screen.findByText('Inflation')).closest('tr')!
  expect(within(row).getAllByText('n/a')).toHaveLength(2)
})

test('409 shows the no-data message', async () => {
  vi.mocked(getScorecard).mockRejectedValue(new ApiError(409, 'No data collected yet for Mexico'))
  renderPage('/?country=MEX')
  expect(await screen.findByText('No data collected yet for Mexico')).toBeInTheDocument()
})

test('source link points to the evidence URL', async () => {
  vi.mocked(getScorecard).mockResolvedValue(colombia)
  renderPage('/?country=COL')
  const link = await screen.findByRole('link', { name: /World Bank/ })
  expect(link).toHaveAttribute('href', 'https://api.worldbank.org/a3')
  expect(link).toHaveTextContent('2025')
})
