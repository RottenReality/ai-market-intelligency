import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createQueryClient } from '@/lib/queryClient'
import type { ComparisonInsight } from '@/lib/types'
import { ComparisonInsightPanel } from './ComparisonInsightPanel'
import { generateComparisonInsight, getComparisonInsight, getProviders } from './api'

vi.mock('./api')

const insight: ComparisonInsight = {
  countries: ['COL', 'MEX'],
  provider: 'groq',
  provider_label: 'Groq',
  model: 'openai/gpt-oss-120b',
  created_at: '2026-11-01T10:00:00+00:00',
  flagged: false,
  overstated: false,
  outdated: false,
  summary: 'Mexico leads with 64% while Colombia trails by 15 points [A1].',
  ranking: [
    { iso3: 'MEX', name: 'Mexico', accessibility: 63.5, rank: 1, explanation: 'Tax treaty in place [A1].' },
    { iso3: 'COL', name: 'Colombia', accessibility: 49.4, rank: 2, explanation: 'No tax treaty [A1].' },
  ],
  key_differences: ['Tax treaty [A1]', 'Working hours [G1]'],
}

function renderPanel(codes: string[]) {
  render(
    <QueryClientProvider client={createQueryClient()}>
      <ComparisonInsightPanel codes={codes} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(getProviders).mockResolvedValue([
    { id: 'openai/gpt-oss-120b', label: 'Groq · GPT-OSS 120B', model: 'openai/gpt-oss-120b' },
    { id: 'qwen/qwen3.8-27b', label: 'Groq · Qwen 3.8 27B', model: 'qwen/qwen3.8-27b' },
  ])
  vi.mocked(getComparisonInsight).mockResolvedValue(null)
})

test('fewer than two countries with data shows the hint and no Generate button', async () => {
  renderPanel(['COL'])
  expect(
    await screen.findByText('Select at least two countries with data to compare them with AI.'),
  ).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Generate' })).not.toBeInTheDocument()
  expect(getComparisonInsight).not.toHaveBeenCalled()
})

test('shows summary, ranking in order with percentages and key differences', async () => {
  vi.mocked(getComparisonInsight).mockResolvedValue(insight)
  renderPanel(['COL', 'MEX'])
  expect(await screen.findByText(insight.summary)).toBeInTheDocument()
  const items = within(screen.getByRole('list', { name: 'Ranking' })).getAllByRole('listitem')
  expect(items[0]).toHaveTextContent('Mexico')
  expect(items[0]).toHaveTextContent('64%')
  expect(items[0]).toHaveTextContent('Tax treaty in place [A1].')
  expect(items[1]).toHaveTextContent('Colombia')
  expect(screen.getByText('Working hours [G1]')).toBeInTheDocument()
  expect(screen.getByText('Written by Groq (openai/gpt-oss-120b) on 2026-11-01')).toBeInTheDocument()
})

test('generate sends the selected codes and provider', async () => {
  vi.mocked(generateComparisonInsight).mockResolvedValue(insight)
  renderPanel(['COL', 'MEX'])
  const user = userEvent.setup()
  await user.selectOptions(await screen.findByLabelText('AI model'), 'qwen/qwen3.8-27b')
  await user.click(screen.getByRole('button', { name: 'Generate' }))
  expect(generateComparisonInsight).toHaveBeenCalledWith(['COL', 'MEX'], 'qwen/qwen3.8-27b')
  expect(await screen.findByText(insight.summary)).toBeInTheDocument()
})

test('flagged and outdated states', async () => {
  vi.mocked(getComparisonInsight).mockResolvedValue({ ...insight, flagged: true, outdated: true })
  renderPanel(['COL', 'MEX'])
  expect(
    await screen.findByText('Some numbers could not be verified; review before use.'),
  ).toBeInTheDocument()
  expect(
    screen.getByText('Written before the latest data or company change. Generate again to update.'),
  ).toBeInTheDocument()
})
