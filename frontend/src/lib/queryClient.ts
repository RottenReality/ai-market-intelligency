import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query'
import { ApiError } from './api'

export const ME_KEY = ['me'] as const

function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401
}

export function createQueryClient(): QueryClient {
  // Any 401 means the session is gone: clear the user so AuthGate sends us to /login.
  const onError = (error: unknown) => {
    if (isUnauthorized(error)) client.setQueryData(ME_KEY, null)
  }
  const client: QueryClient = new QueryClient({
    queryCache: new QueryCache({ onError }),
    mutationCache: new MutationCache({ onError }),
    defaultOptions: {
      queries: {
        retry: (failures, error) =>
          !(error instanceof ApiError && error.status < 500) && failures < 2,
        refetchOnWindowFocus: false,
      },
    },
  })
  return client
}
