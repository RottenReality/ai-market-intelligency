import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { ApiError } from '@/lib/api'
import type { Profile, ProfileEdits } from '@/lib/types'
import { getProfile, resetProfile, saveProfile } from './api'

const MAX_DESCRIPTION = 4000
const LANGUAGE_NAMES: Record<string, string> = {
  en: 'English', es: 'Spanish', pt: 'Portuguese', fr: 'French', de: 'German', it: 'Italian',
}
const CHANNEL_NAMES: Record<string, string> = { sms: 'SMS', email: 'Email', whatsapp: 'WhatsApp' }

function toEdits(profile: Profile): ProfileEdits {
  const { name, description, supported_languages, channels } = profile
  return { name, description, supported_languages, channels }
}

function errorText(error: unknown): string {
  if (error instanceof ApiError) return error.detail
  return 'Could not save the profile. Please try again.'
}

export function CompanyPage() {
  const profile = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  if (profile.isPending) return <p className="text-sm text-muted-foreground">Loading…</p>
  if (profile.isError) return <p role="alert" className="text-destructive">Could not load the company profile.</p>
  return <CompanyForm profile={profile.data} />
}

function CompanyForm({ profile }: { profile: Profile }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<ProfileEdits>(() => toEdits(profile))
  const [saved, setSaved] = useState(false)

  function afterChange(updated: Profile) {
    queryClient.setQueryData(['profile'], updated)
    setForm(toEdits(updated))
    // Languages and channels change C1/C2, and the description changes the AI analyses.
    for (const key of ['scorecard', 'comparison', 'analysis', 'insight']) {
      void queryClient.invalidateQueries({ queryKey: [key] })
    }
  }

  const save = useMutation({
    mutationFn: () => saveProfile(form),
    onSuccess: (updated) => {
      afterChange(updated)
      setSaved(true)
    },
  })
  const reset = useMutation({ mutationFn: resetProfile, onSuccess: afterChange })

  function toggle(field: 'supported_languages' | 'channels', value: string) {
    setSaved(false)
    setForm((current) => {
      const values = current[field]
      return {
        ...current,
        [field]: values.includes(value) ? values.filter((v) => v !== value) : [...values, value],
      }
    })
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    save.mutate()
  }

  function onReset() {
    if (window.confirm('Reset the company profile to the default one? Your edits will be lost.')) {
      setSaved(false)
      reset.mutate()
    }
  }

  const canSave =
    form.name.trim() !== '' &&
    form.supported_languages.length > 0 &&
    form.channels.length > 0 &&
    !save.isPending

  return (
    <section className="flex max-w-3xl flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Company profile</h1>
        <p className="text-sm text-muted-foreground">
          Used for the language (C1) and channel (C2) indicators and as background for the AI
          analysis. {profile.source === 'saved' ? 'Showing your saved edits.' : 'Showing the default profile.'}
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Company</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-5" onSubmit={onSubmit}>
            <div className="flex flex-col gap-2">
              <Label htmlFor="company-name">Name</Label>
              <Input
                id="company-name"
                value={form.name}
                maxLength={120}
                onChange={(e) => {
                  setSaved(false)
                  setForm({ ...form, name: e.target.value })
                }}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="company-description">Description</Label>
              <Textarea
                id="company-description"
                rows={8}
                value={form.description}
                maxLength={MAX_DESCRIPTION}
                onChange={(e) => {
                  setSaved(false)
                  setForm({ ...form, description: e.target.value })
                }}
              />
              <span className="self-end text-xs text-muted-foreground">
                {form.description.length}/{MAX_DESCRIPTION}
              </span>
            </div>
            <CheckboxGroup
              legend="Languages the company sells and gives support in"
              options={profile.options.languages}
              names={LANGUAGE_NAMES}
              selected={form.supported_languages}
              onToggle={(value) => toggle('supported_languages', value)}
            />
            <CheckboxGroup
              legend="Channels the company's product uses"
              options={profile.options.channels}
              names={CHANNEL_NAMES}
              selected={form.channels}
              onToggle={(value) => toggle('channels', value)}
            />
            <div className="rounded-md bg-muted p-3 text-sm">
              <p>
                Home country: <b>{profile.home_country}</b> · Home time zone:{' '}
                <b>{profile.home_timezone}</b>
              </p>
              <p className="text-muted-foreground">
                Changing the home country needs new reference data; edit
                backend/config/company.yaml and run collect.
              </p>
            </div>
            {save.isError && (
              <p role="alert" className="text-sm text-destructive">
                {errorText(save.error)}
              </p>
            )}
            <div className="flex flex-wrap items-center gap-3">
              <Button type="submit" disabled={!canSave}>
                Save
              </Button>
              <Button type="button" variant="outline" onClick={onReset} disabled={reset.isPending}>
                Reset to the default profile
              </Button>
              {saved && <span className="text-sm text-muted-foreground">Saved</span>}
            </div>
          </form>
        </CardContent>
      </Card>
    </section>
  )
}

interface CheckboxGroupProps {
  legend: string
  options: string[]
  names: Record<string, string>
  selected: string[]
  onToggle: (value: string) => void
}

function CheckboxGroup({ legend, options, names, selected, onToggle }: CheckboxGroupProps) {
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-1 text-sm font-medium">{legend}</legend>
      <div className="flex flex-wrap gap-x-5 gap-y-2">
        {options.map((option) => (
          <label key={option} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              className="size-4 accent-primary"
              checked={selected.includes(option)}
              onChange={() => onToggle(option)}
            />
            {names[option] ?? option}
          </label>
        ))}
      </div>
    </fieldset>
  )
}
