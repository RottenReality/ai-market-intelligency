import { apiFetch } from '@/lib/api'

export function getHealth(): Promise<{ status: string }> {
  return apiFetch('/api/health')
}
