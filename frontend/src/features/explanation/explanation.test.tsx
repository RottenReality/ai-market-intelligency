import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ApiError } from '@/lib/api'
import { createQueryClient } from '@/lib/queryClient'
import { ExplanationPanel } from './ExplanationPanel'
import { createExplanation, getExplanation } from './api'

vi.mock('./api')

const explanation = {
  iso3: 'COL',
  text: 'Colombia scores 56% overall. Administrative is the weakest dimension [A1].',
  flagged: false,
  created_at: '2026-10-25T10:00:00+00:00',
}

function renderPanel() {
  render(
    <QueryClientProvider client={createQueryClient()}>
      <ExplanationPanel iso3="COL" />
    </QueryClientProvider>,
  )
}

test('shows cached explanation on load', async () => {
  vi.mocked(getExplanation).mockResolvedValue(explanation)
  renderPanel()
  expect(await screen.findByText(explanation.text)).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Explain' })).not.toBeInTheDocument()
})

test('explain button generates and shows text', async () => {
  vi.mocked(getExplanation).mockResolvedValue(null)
  vi.mocked(createExplanation).mockResolvedValue(explanation)
  renderPanel()
  await userEvent.click(await screen.findByRole('button', { name: 'Explain' }))
  expect(await screen.findByText(explanation.text)).toBeInTheDocument()
  expect(createExplanation).toHaveBeenCalledWith('COL')
})

test('flagged explanation shows a review warning', async () => {
  vi.mocked(getExplanation).mockResolvedValue({ ...explanation, flagged: true })
  renderPanel()
  expect(
    await screen.findByText('Some numbers could not be verified. Review before using.'),
  ).toBeInTheDocument()
})

test('503 shows "AI is not configured"', async () => {
  vi.mocked(getExplanation).mockResolvedValue(null)
  vi.mocked(createExplanation).mockRejectedValue(new ApiError(503, 'AI is not configured'))
  renderPanel()
  await userEvent.click(await screen.findByRole('button', { name: 'Explain' }))
  expect(await screen.findByText('AI is not configured')).toBeInTheDocument()
})

test('502 shows a retry message', async () => {
  vi.mocked(getExplanation).mockResolvedValue(null)
  vi.mocked(createExplanation).mockRejectedValue(new ApiError(502, 'The AI service failed'))
  renderPanel()
  await userEvent.click(await screen.findByRole('button', { name: 'Explain' }))
  expect(await screen.findByText('The AI service failed. Try again.')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Explain' })).toBeEnabled()
})
