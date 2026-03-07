'use client'

import { useState, useCallback, useMemo } from 'react'
import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Skeleton } from '@/components/ui/Skeleton'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs'
import { cn } from '@/lib/cn'
import { useSettings, useSaveSettings } from '@/hooks/useSettings'
import type { SettingsField, SettingsSection } from '@/lib/api/endpoints/settings'

const TAB_LABELS: Record<string, string> = {
  agent: 'Agent',
  external: 'Services',
  developer: 'Developer',
  mcp: 'MCP',
}

const TAB_ORDER = ['agent', 'external', 'developer', 'mcp']

function stripScriptTags(html: string): string {
  return html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
}

function SettingsFieldRenderer({
  field,
  currentValue,
  onChange,
}: {
  field: SettingsField
  currentValue: unknown
  onChange: (id: string, value: unknown) => void
}) {
  const value = currentValue ?? field.value

  switch (field.type) {
    case 'text':
      return (
        <Input
          type="text"
          value={String(value ?? '')}
          onChange={(e) => onChange(field.id, e.target.value)}
        />
      )

    case 'number':
      return (
        <Input
          type="number"
          value={value === '' || value == null ? '' : String(value)}
          min={field.min}
          max={field.max}
          step={field.step}
          onChange={(e) => {
            const v = e.target.value
            onChange(field.id, v === '' ? '' : Number(v))
          }}
        />
      )

    case 'password':
      return (
        <Input
          type="password"
          value={String(value ?? '')}
          onChange={(e) => onChange(field.id, e.target.value)}
        />
      )

    case 'select':
      return (
        <select
          value={String(value ?? '')}
          onChange={(e) => onChange(field.id, e.target.value)}
          className={cn(
            'flex h-9 w-full rounded-md border bg-[var(--surface-primary)] px-3 py-1 text-sm',
            'border-[var(--border-default)] text-[var(--text-primary)]',
            'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent',
          )}
        >
          {field.options?.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      )

    case 'range': {
      const numValue = Number(value ?? field.min ?? 0)
      return (
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={field.min}
            max={field.max}
            step={field.step}
            value={numValue}
            onChange={(e) => onChange(field.id, Number(e.target.value))}
            className="flex-1"
          />
          <span className="text-sm font-mono text-[var(--text-secondary)] min-w-[3rem] text-right">
            {numValue}
          </span>
        </div>
      )
    }

    case 'textarea':
      return (
        <textarea
          value={String(value ?? '')}
          onChange={(e) => onChange(field.id, e.target.value)}
          style={field.style ? parseStyle(field.style) : undefined}
          rows={4}
          className={cn(
            'flex w-full rounded-md border bg-[var(--surface-primary)] px-3 py-2 text-sm',
            'border-[var(--border-default)] text-[var(--text-primary)]',
            'placeholder:text-[var(--text-tertiary)]',
            'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent',
            'resize-y',
          )}
        />
      )

    case 'switch': {
      const checked = Boolean(value)
      return (
        <button
          type="button"
          role="switch"
          aria-checked={checked}
          onClick={() => onChange(field.id, !checked)}
          className={cn(
            'relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent',
            'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
            checked ? 'bg-brand-600' : 'bg-slate-300 dark:bg-slate-600',
          )}
        >
          <span
            className={cn(
              'pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-sm',
              'transition-transform',
              checked ? 'translate-x-5' : 'translate-x-0',
            )}
          />
        </button>
      )
    }

    case 'button':
      return (
        <Button variant="secondary" size="sm">
          {field.title}
        </Button>
      )

    case 'html':
      return null

    default:
      return null
  }
}

function parseStyle(style: string): React.CSSProperties {
  const obj: Record<string, string> = {}
  for (const part of style.split(';')) {
    const [key, val] = part.split(':').map((s) => s.trim())
    if (key && val) {
      const camelKey = key.replace(/-([a-z])/g, (_, c: string) => c.toUpperCase())
      obj[camelKey] = val
    }
  }
  return obj
}

function SectionCard({
  section,
  dirtyValues,
  onChange,
}: {
  section: SettingsSection
  dirtyValues: Record<string, unknown>
  onChange: (id: string, value: unknown) => void
}) {
  const visibleFields = section.fields.filter((f) => !f.hidden && f.type !== 'html')
  if (visibleFields.length === 0) return null

  return (
    <Card>
      <CardHeader>
        <h3 className="font-semibold text-[var(--text-primary)]">{section.title}</h3>
        {section.description && (
          <p className="text-sm text-[var(--text-secondary)] mt-0.5">{section.description}</p>
        )}
      </CardHeader>
      <CardBody>
        <div className="space-y-5">
          {visibleFields.map((field) => {
            const sanitizedDesc = field.description ? stripScriptTags(field.description) : ''
            return (
              <div
                key={field.id}
                className="grid grid-cols-1 md:grid-cols-[1fr_1fr] gap-x-6 gap-y-2 items-start"
              >
                <div className="min-w-0">
                  <label className="text-sm font-medium text-[var(--text-primary)]">
                    {field.title}
                  </label>
                  {sanitizedDesc && (
                    <p
                      className="text-xs text-[var(--text-tertiary)] mt-0.5"
                      dangerouslySetInnerHTML={{ __html: sanitizedDesc }}
                    />
                  )}
                </div>
                <div className="min-w-0">
                  <SettingsFieldRenderer
                    field={field}
                    currentValue={field.id in dirtyValues ? dirtyValues[field.id] : undefined}
                    onChange={onChange}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </CardBody>
    </Card>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-72" />
      </div>
      <Skeleton className="h-10 w-96" />
      {[1, 2, 3].map((i) => (
        <div key={i} className="rounded-lg border border-[var(--border-default)] p-4 space-y-4">
          <Skeleton className="h-5 w-40" />
          {[1, 2, 3].map((j) => (
            <div key={j} className="grid grid-cols-2 gap-4">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-9 w-full" />
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

export default function GeneralSettingsPage() {
  const { data, isLoading, error } = useSettings()
  const saveMutation = useSaveSettings()
  const [dirtyValues, setDirtyValues] = useState<Record<string, unknown>>({})

  const handleChange = useCallback((id: string, value: unknown) => {
    setDirtyValues((prev) => ({ ...prev, [id]: value }))
  }, [])

  const handleSave = useCallback(() => {
    if (Object.keys(dirtyValues).length === 0) return
    saveMutation.mutate(dirtyValues, {
      onSuccess: () => setDirtyValues({}),
    })
  }, [dirtyValues, saveMutation])

  const handleDiscard = useCallback(() => {
    setDirtyValues({})
  }, [])

  const sectionsByTab = useMemo(() => {
    if (!data?.settings?.sections) return {}
    const map: Record<string, SettingsSection[]> = {}
    for (const section of data.settings.sections) {
      const tab = section.tab || 'agent'
      if (!map[tab]) map[tab] = []
      map[tab].push(section)
    }
    return map
  }, [data])

  const availableTabs = useMemo(
    () => TAB_ORDER.filter((t) => sectionsByTab[t]?.length),
    [sectionsByTab],
  )

  const hasDirtyValues = Object.keys(dirtyValues).length > 0

  if (isLoading) return <LoadingSkeleton />

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">General Settings</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">Agent configuration and model preferences</p>
        </div>
        <Card>
          <CardBody>
            <p className="text-sm text-danger">Failed to load settings. Please try again.</p>
          </CardBody>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-20">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">General Settings</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">Agent configuration and model preferences</p>
      </div>

      <Tabs defaultValue={availableTabs[0] || 'agent'}>
        <TabsList>
          {availableTabs.map((tab) => (
            <TabsTrigger key={tab} value={tab}>
              {TAB_LABELS[tab] || tab}
            </TabsTrigger>
          ))}
        </TabsList>

        {availableTabs.map((tab) => (
          <TabsContent key={tab} value={tab}>
            <div className="space-y-6">
              {sectionsByTab[tab]?.map((section) => (
                <SectionCard
                  key={section.id}
                  section={section}
                  dirtyValues={dirtyValues}
                  onChange={handleChange}
                />
              ))}
            </div>
          </TabsContent>
        ))}
      </Tabs>

      {hasDirtyValues && (
        <div
          className={cn(
            'fixed bottom-0 left-0 right-0 z-50',
            'border-t border-[var(--border-default)] bg-[var(--surface-primary)]',
            'px-6 py-3 shadow-lg',
          )}
        >
          <div className="mx-auto max-w-5xl flex items-center justify-between">
            <p className="text-sm text-[var(--text-secondary)]">
              You have unsaved changes ({Object.keys(dirtyValues).length} field
              {Object.keys(dirtyValues).length === 1 ? '' : 's'})
            </p>
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="sm" onClick={handleDiscard}>
                Discard
              </Button>
              <Button
                size="sm"
                onClick={handleSave}
                loading={saveMutation.isPending}
              >
                Save changes
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
