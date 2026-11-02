import { ApiError } from '@/lib/api'

/** The server's message for known AI errors (quota, rejected key, unreadable answer...). */
export function aiErrorText(error: unknown): string {
  if (error instanceof ApiError && [400, 422, 429, 502, 503].includes(error.status)) {
    return error.detail
  }
  return 'Could not generate the AI analysis. Try again.'
}
