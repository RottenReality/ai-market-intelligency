import type { ProviderInfo } from '@/lib/types'

interface Props {
  providers: ProviderInfo[]
  value: string
  onChange: (provider: string) => void
}

export function ProviderSelect({ providers, value, onChange }: Props) {
  return (
    <label className="flex items-center gap-2 text-sm">
      <span>AI provider</span>
      <select
        aria-label="AI provider"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-9 rounded-md border border-input bg-background px-2 text-sm shadow-xs"
      >
        {providers.map((p) => (
          <option key={p.id} value={p.id}>
            {p.label} ({p.model})
          </option>
        ))}
      </select>
    </label>
  )
}
