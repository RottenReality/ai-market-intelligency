import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ApiError } from '@/lib/api'
import { createQueryClient } from '@/lib/queryClient'
import type { CountryAnalysis, ProviderInfo } from '@/lib/types'
import { AnalysisPanel } from './AnalysisPanel'
import { generateCountryAnalysis, getCountryAnalysis, getProviders } from './api'

vi.mock('./api')

const providers: ProviderInfo[] = [
  { id: 'openai/gpt-oss-120b', label: 'Groq · GPT-OSS 120B', model: 'openai/gpt-oss-120b' },
  { id: 'qwen/qwen3.8-27b', label: 'Groq · Qwen 3.8 27B', model: 'qwen/qwen3.8-27b' },
]

const analysis: CountryAnalysis = {
  iso3: 'COL',
  provider: 'groq',
  provider_label: 'Groq',
  model: 'openai/gpt-oss-120b',
  created_at: '2026-11-01T10:00:00+00:00',
  flagged: false,
  outdated: false,
  content: {
    executive_summary: 'Colombia scores 52% overall [A1].',
    dimensions: {
      Cultural: 'Cultural text [C3].',
      Administrative: 'Administrative text [A1].',
      Geographic: 'Geographic text [G1].',
      Economic: 'Economic text [E2].',
    },
    barriers: ['No tax treaty [A1]'],
    opportunities: ['Large cities [E2]'],
    recommendation: 'Explore a local partner first.',
  },
}

function renderPanel() {
  render(
    <QueryClientProvider client={createQueryClient()}>
      <AnalysisPanel iso3="COL" />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(getProviders).mockResolvedValue(providers)
  vi.mocked(getCountryAnalysis).mockResolvedValue(null)
})

test('no providers shows "AI is not configured" and no Generate button', async () => {
  vi.mocked(getProviders).mockResolvedValue([])
  renderPanel()
  expect(await screen.findByText('AI is not configured')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Generate' })).not.toBeInTheDocument()
})

test('shows saved analysis sections and attribution', async () => {
  vi.mocked(getCountryAnalysis).mockResolvedValue(analysis)
  renderPanel()
  expect(await screen.findByText('Colombia scores 52% overall [A1].')).toBeInTheDocument()
  for (const heading of ['Executive summary', 'Cultural', 'Administrative', 'Geographic',
    'Economic', 'Barriers', 'Opportunities', 'Recommendation']) {
    expect(screen.getByRole('heading', { name: heading })).toBeInTheDocument()
  }
  expect(screen.getByText('No tax treaty [A1]')).toBeInTheDocument()
  expect(screen.getByText('Written by Groq (openai/gpt-oss-120b) on 2026-11-01')).toBeInTheDocument()
})

test('generate uses the chosen provider', async () => {
  vi.mocked(generateCountryAnalysis).mockResolvedValue({ ...analysis, provider: 'groq' })
  renderPanel()
  const user = userEvent.setup()
  await user.selectOptions(await screen.findByLabelText('AI model'), 'qwen/qwen3.8-27b')
  await user.click(screen.getByRole('button', { name: 'Generate' }))
  expect(generateCountryAnalysis).toHaveBeenCalledWith('COL', 'qwen/qwen3.8-27b')
  expect(await screen.findByText('Colombia scores 52% overall [A1].')).toBeInTheDocument()
})

test('flagged shows the review warning', async () => {
  vi.mocked(getCountryAnalysis).mockResolvedValue({ ...analysis, flagged: true })
  renderPanel()
  expect(
    await screen.findByText('Some numbers could not be verified; review before use.'),
  ).toBeInTheDocument()
})

test('outdated shows the badge', async () => {
  vi.mocked(getCountryAnalysis).mockResolvedValue({ ...analysis, outdated: true })
  renderPanel()
  expect(
    await screen.findByText(
      'Written before the latest data or company change. Generate again to update.',
    ),
  ).toBeInTheDocument()
})

test('quota error keeps the saved analysis visible and shows the message', async () => {
  const message = "Groq's free limit for GPT-OSS 120B was reached. Wait a minute and try again, or use Qwen 3.8 27B."
  vi.mocked(getCountryAnalysis).mockResolvedValue(analysis)
  vi.mocked(generateCountryAnalysis).mockRejectedValue(new ApiError(429, message))
  renderPanel()
  await userEvent.click(await screen.findByRole('button', { name: 'Generate' }))
  expect(await screen.findByText(message)).toBeInTheDocument()
  expect(screen.getByText('Colombia scores 52% overall [A1].')).toBeInTheDocument()
})

test('unreadable answer shows the error and re-enables Generate', async () => {
  vi.mocked(generateCountryAnalysis).mockRejectedValue(
    new ApiError(502, 'The AI returned an unreadable answer. Try again.'),
  )
  renderPanel()
  await userEvent.click(await screen.findByRole('button', { name: 'Generate' }))
  expect(
    await screen.findByText('The AI returned an unreadable answer. Try again.'),
  ).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Generate' })).toBeEnabled()
})

test('the model selector lists each Groq model by name', async () => {
  renderPanel()
  const select = await screen.findByLabelText('AI model')
  const options = within(select).getAllByRole('option').map((option) => option.textContent)
  expect(options).toEqual(['Groq · GPT-OSS 120B', 'Groq · Qwen 3.8 27B'])
})
