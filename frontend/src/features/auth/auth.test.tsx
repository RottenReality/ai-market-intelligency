import { QueryClientProvider, useQuery } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router'
import { ApiError } from '@/lib/api'
import { createQueryClient } from '@/lib/queryClient'
import { AppShell } from './AppShell'
import { AuthGate } from './AuthGate'
import { LoginPage } from './LoginPage'
import { getMe, login, logout } from './api'

vi.mock('./api')
vi.mock('@/features/health/api', () => ({ getHealth: vi.fn().mockResolvedValue({ status: 'ok' }) }))

function Home() {
  return <p>Home content</p>
}

function ExpiringQuery() {
  useQuery({
    queryKey: ['expiring'],
    queryFn: () => Promise.reject(new ApiError(401, 'Not authenticated')),
  })
  return <p>Data page</p>
}

function renderApp(initialPath = '/', page = <Home />) {
  render(
    <QueryClientProvider client={createQueryClient()}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<AuthGate />}>
            <Route element={<AppShell />}>
              <Route index element={page} />
            </Route>
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

async function submitLogin(username: string, password: string) {
  const user = userEvent.setup()
  await user.type(await screen.findByLabelText('Username'), username)
  await user.type(screen.getByLabelText('Password'), password)
  await user.click(screen.getByRole('button', { name: 'Sign in' }))
}

beforeEach(() => {
  vi.mocked(getMe).mockReset()
  vi.mocked(login).mockReset()
  vi.mocked(logout).mockReset()
})

test('visiting "/" without a session redirects to the login page', async () => {
  vi.mocked(getMe).mockRejectedValue(new ApiError(401, 'Not authenticated'))
  renderApp('/')
  expect(await screen.findByLabelText('Username')).toBeInTheDocument()
})

test('wrong credentials show "Invalid username or password"', async () => {
  vi.mocked(getMe).mockRejectedValue(new ApiError(401, 'Not authenticated'))
  vi.mocked(login).mockRejectedValue(new ApiError(401, 'Invalid username or password'))
  renderApp('/login')
  await submitLogin('admin', 'wrong')
  expect(await screen.findByText('Invalid username or password')).toBeInTheDocument()
})

test('429 shows the lockout message', async () => {
  vi.mocked(getMe).mockRejectedValue(new ApiError(401, 'Not authenticated'))
  vi.mocked(login).mockRejectedValue(
    new ApiError(429, 'Too many failed attempts. Try again in 15 minutes.'),
  )
  renderApp('/login')
  await submitLogin('admin', 'wrong')
  expect(
    await screen.findByText('Too many failed attempts. Try again in 15 minutes.'),
  ).toBeInTheDocument()
})

test('successful login navigates to the app shell', async () => {
  vi.mocked(getMe)
    .mockRejectedValueOnce(new ApiError(401, 'Not authenticated'))
    .mockResolvedValue({ username: 'admin' })
  vi.mocked(login).mockResolvedValue(undefined)
  renderApp('/login')
  await submitLogin('admin', 'correct horse')
  expect(await screen.findByText('Home content')).toBeInTheDocument()
  expect(screen.getByText('admin')).toBeInTheDocument()
  expect(login).toHaveBeenCalledWith('admin', 'correct horse')
})

test('a 401 from any later query redirects to login', async () => {
  vi.mocked(getMe).mockResolvedValue({ username: 'admin' })
  renderApp('/', <ExpiringQuery />)
  expect(await screen.findByLabelText('Username')).toBeInTheDocument()
})

test('logout returns to the login page', async () => {
  vi.mocked(getMe).mockResolvedValue({ username: 'admin' })
  vi.mocked(logout).mockResolvedValue(undefined)
  renderApp('/')
  const user = userEvent.setup()
  await user.click(await screen.findByRole('button', { name: 'Log out' }))
  expect(await screen.findByLabelText('Username')).toBeInTheDocument()
})
