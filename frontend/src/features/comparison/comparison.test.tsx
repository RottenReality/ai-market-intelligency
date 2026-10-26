import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router'
import { createQueryClient } from '@/lib/queryClient'
import type { Comparison } from '@/lib/types'
import { getCountries } from '@/features/scorecard/api'
import { ComparisonPage } from './ComparisonPage'
import { getComparison } from './api'

vi.mock('./api')
vi.mock('@/features/scorecard/api')

const dims = (c: number, a: number, g: number, e: number) => ({ C: c, A: a, G: g, E: e })

const comparison: Comparison = {
  countries: [
    { iso3: 'MEX', name: 'Mexico', has_data: true, accessibility: 61.4, dimensions: dims(40, 70, 75, 60), indicators_available: 9, indicators_total: 12 },
    { iso3: 'COL', name: 'Colombia', has_data: true, accessibility: 55.7, dimensions: dims(37, 49, 71, 66), indicators_available: 10, indicators_total: 12 },
    { iso3: 'CHL', name: 'Chile', has_data: false, accessibility: null, dimensions: { C: null, A: null, G: null, E: null }, indicators_available: 0, indicators_total: 12 },
  ],
}

function LocationProbe() {
  return <p data-testid="search">{useLocation().search}</p>
}

function renderPage(path = '/compare') {
  render(
    <QueryClientProvider client={createQueryClient()}>
      <MemoryRouter initialEntries={[path]}>
        <ComparisonPage />
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(getCountries).mockResolvedValue([
    { iso3: 'COL', name: 'Colombia', has_data: true },
    { iso3: 'MEX', name: 'Mexico', has_data: true },
    { iso3: 'ESP', name: 'Spain', has_data: true },
    { iso3: 'CHL', name: 'Chile', has_data: false },
  ])
  vi.mocked(getComparison).mockResolvedValue(comparison)
})

test('selected countries appear in ranking order with percentages', async () => {
  renderPage('/compare?iso3=COL,MEX,CHL')
  const table = await screen.findByRole('table', { name: 'Comparison values' })
  const rows = within(table).getAllByRole('row').slice(1)
  expect(within(rows[0]).getByText('Mexico')).toBeInTheDocument()
  expect(within(rows[0]).getByText('61%')).toBeInTheDocument()
  expect(within(rows[1]).getByText('Colombia')).toBeInTheDocument()
  expect(within(rows[1]).getByText('56%')).toBeInTheDocument()
})

test('country without data shows "no data"', async () => {
  renderPage('/compare?iso3=COL,MEX,CHL')
  const table = await screen.findByRole('table', { name: 'Comparison values' })
  const chile = within(table).getByText('Chile').closest('tr')!
  expect(within(chile).getByText('no data')).toBeInTheDocument()
})

test('radar overlays at most three countries and says so when more are selected', async () => {
  vi.mocked(getComparison).mockResolvedValue({
    countries: [
      ...comparison.countries.slice(0, 2),
      { iso3: 'ESP', name: 'Spain', has_data: true, accessibility: 50, dimensions: dims(50, 50, 50, 50), indicators_available: 12, indicators_total: 12 },
      { iso3: 'CHL', name: 'Chile', has_data: true, accessibility: 45, dimensions: dims(45, 45, 45, 45), indicators_available: 12, indicators_total: 12 },
    ],
  })
  renderPage('/compare?iso3=COL,MEX,ESP,CHL')
  expect(
    await screen.findByText('The radar shows the first 3 countries in the ranking.'),
  ).toBeInTheDocument()
})

test('selection is kept in the URL and drives the request', async () => {
  renderPage('/compare')
  const user = userEvent.setup()
  await user.click(await screen.findByRole('checkbox', { name: 'Colombia' }))
  await user.click(screen.getByRole('checkbox', { name: 'Mexico' }))
  expect(screen.getByTestId('search')).toHaveTextContent('?iso3=COL%2CMEX')
  await screen.findByRole('table', { name: 'Comparison values' })
  expect(getComparison).toHaveBeenLastCalledWith(['COL', 'MEX'])
})

test('nothing selected shows a hint and does not call the API', async () => {
  renderPage('/compare')
  expect(await screen.findByText('Select countries to compare.')).toBeInTheDocument()
  expect(getComparison).not.toHaveBeenCalled()
})

test('shows data coverage and warns when countries have different coverage', async () => {
  renderPage('/compare?iso3=COL,MEX,CHL')
  const table = await screen.findByRole('table', { name: 'Comparison values' })
  const colombia = within(table).getByText('Colombia').closest('tr')!
  expect(within(colombia).getByText('10/12')).toBeInTheDocument()
  expect(
    screen.getByText(
      'Countries have different amounts of data. Missing indicators are left out of the averages, so compare with care.',
    ),
  ).toBeInTheDocument()
})
