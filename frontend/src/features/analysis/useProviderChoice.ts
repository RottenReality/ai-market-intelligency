import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { getProviders } from './api'

const STORAGE_KEY = 'ai-provider'

function remembered(): string | null {
  try {
    return window.localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

/** Available providers plus the chosen one, remembering the last choice when possible. */
export function useProviderChoice() {
  const providers = useQuery({ queryKey: ['ai-providers'], queryFn: getProviders })
  const [choice, setChoice] = useState<string | null>(remembered)
  const list = providers.data ?? []
  const selected = list.some((p) => p.id === choice) ? (choice as string) : (list[0]?.id ?? '')

  function choose(provider: string) {
    setChoice(provider)
    try {
      window.localStorage.setItem(STORAGE_KEY, provider)
    } catch {
      // Storage can be unavailable (private mode); the choice still works for this visit.
    }
  }

  return { providers, list, selected, choose }
}
