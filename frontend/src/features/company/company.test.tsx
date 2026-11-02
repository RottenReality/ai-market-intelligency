import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ApiError } from '@/lib/api'
import { createQueryClient } from '@/lib/queryClient'
import type { Profile } from '@/lib/types'
import { CompanyPage } from './CompanyPage'
import { getProfile, resetProfile, saveProfile } from './api'

vi.mock('./api')

const profile: Profile = {
  name: 'Example Restaurant Marketing Co.',
  description: 'A fictional company.',
  supported_languages: ['en'],
  channels: ['sms', 'email'],
  home_country: 'USA',
  home_timezone: 'America/Los_Angeles',
  source: 'file',
  options: { languages: ['en', 'es', 'pt', 'fr', 'de', 'it'], channels: ['sms', 'email', 'whatsapp'] },
}

function renderPage() {
  render(
    <QueryClientProvider client={createQueryClient()}>
      <CompanyPage />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(getProfile).mockResolvedValue(profile)
})

test('shows the profile values and the read-only home country', async () => {
  renderPage()
  expect(await screen.findByLabelText('Name')).toHaveValue('Example Restaurant Marketing Co.')
  expect(screen.getByLabelText('Description')).toHaveValue('A fictional company.')
  expect(screen.getByRole('checkbox', { name: 'English' })).toBeChecked()
  expect(screen.getByRole('checkbox', { name: 'Spanish' })).not.toBeChecked()
  expect(screen.getByText(/USA/)).toBeInTheDocument()
  expect(screen.getByText(/America\/Los_Angeles/)).toBeInTheDocument()
  expect(screen.queryByLabelText('Home country')).not.toBeInTheDocument()
})

test('saving sends the edited fields and shows "Saved"', async () => {
  vi.mocked(saveProfile).mockResolvedValue({ ...profile, name: 'Real Co.', source: 'saved' })
  renderPage()
  const user = userEvent.setup()
  const name = await screen.findByLabelText('Name')
  await user.clear(name)
  await user.type(name, 'Real Co.')
  await user.click(screen.getByRole('checkbox', { name: 'Spanish' }))
  await user.click(screen.getByRole('button', { name: 'Save' }))
  expect(saveProfile).toHaveBeenCalledWith({
    name: 'Real Co.',
    description: 'A fictional company.',
    supported_languages: ['en', 'es'],
    channels: ['sms', 'email'],
  })
  expect(await screen.findByText('Saved')).toBeInTheDocument()
})

test('validation error from the server is shown', async () => {
  vi.mocked(saveProfile).mockRejectedValue(new ApiError(422, 'name must be 1-120 characters'))
  renderPage()
  await userEvent.click(await screen.findByRole('button', { name: 'Save' }))
  expect(await screen.findByText(/name must be 1-120 characters/)).toBeInTheDocument()
})

test('reset asks for confirmation and restores the default profile', async () => {
  vi.mocked(getProfile).mockResolvedValue({ ...profile, name: 'Real Co.', source: 'saved' })
  vi.mocked(resetProfile).mockResolvedValue(profile)
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  renderPage()
  await userEvent.click(await screen.findByRole('button', { name: 'Reset to the default profile' }))
  expect(window.confirm).toHaveBeenCalled()
  expect(resetProfile).toHaveBeenCalled()
  expect(await screen.findByDisplayValue('Example Restaurant Marketing Co.')).toBeInTheDocument()
})

test('at least one language and one channel must stay ticked', async () => {
  renderPage()
  await userEvent.click(await screen.findByRole('checkbox', { name: 'English' }))
  expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()
})
