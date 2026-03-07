'use client'

import { useState } from 'react'
import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Shield, Key, Save } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api/client'

interface SettingsField {
  id: string
  title: string
  description: string
  type: string
  value: unknown
  options?: Array<{ value: string; label: string }>
  hidden?: boolean
}

interface SettingsSection {
  id: string
  title: string
  description: string
  tab: string
  fields: SettingsField[]
}

function useSecuritySettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: () => api<{ settings: { sections: SettingsSection[] } }>('settings_get', { method: 'GET' }),
    select: (data) => {
      const sections = data.settings.sections.filter(
        (s) => s.id === 'auth' || s.id === 'api_keys' || s.id === 'secrets' || s.id === 'passkey_security'
      )
      return sections
    },
  })
}

export default function SecuritySettingsPage() {
  const { data: sections, isLoading } = useSecuritySettings()
  const qc = useQueryClient()
  const [changes, setChanges] = useState<Record<string, unknown>>({})

  const saveMutation = useMutation({
    mutationFn: (values: Record<string, unknown>) => api('settings_set', { body: values }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['settings'] })
      setChanges({})
    },
  })

  const handleChange = (fieldId: string, value: unknown) => {
    setChanges((prev) => ({ ...prev, [fieldId]: value }))
  }

  const handleSave = () => {
    if (Object.keys(changes).length > 0) {
      saveMutation.mutate(changes)
    }
  }

  const hasChanges = Object.keys(changes).length > 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Security</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">Authentication, API keys, and secrets management</p>
        </div>
        {hasChanges && (
          <Button size="sm" onClick={handleSave} disabled={saveMutation.isPending}>
            <Save className="h-3.5 w-3.5" />
            {saveMutation.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-40 w-full" />)}
        </div>
      ) : (
        sections?.map((section) => (
          <Card key={section.id}>
            <CardHeader>
              <div className="flex items-center gap-2">
                {section.id === 'auth' && <Shield className="h-4 w-4 text-brand-500" />}
                {section.id === 'api_keys' && <Key className="h-4 w-4 text-brand-500" />}
                <h2 className="font-semibold text-[var(--text-primary)]">{section.title}</h2>
              </div>
              <p className="text-xs text-[var(--text-secondary)] mt-1">{stripHtml(section.description)}</p>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                {section.fields
                  .filter((f) => !f.hidden && f.type !== 'html' && f.type !== 'button')
                  .map((field) => (
                    <div key={field.id} className="grid grid-cols-1 md:grid-cols-3 gap-2 items-start">
                      <div>
                        <p className="text-sm font-medium text-[var(--text-primary)]">{field.title}</p>
                        <p className="text-xs text-[var(--text-secondary)]">{stripHtml(field.description)}</p>
                      </div>
                      <div className="md:col-span-2">
                        {field.type === 'password' && (
                          <Input
                            type="password"
                            value={changes[field.id] !== undefined ? String(changes[field.id]) : String(field.value ?? '')}
                            onChange={(e) => handleChange(field.id, e.target.value)}
                            placeholder="Enter value..."
                          />
                        )}
                        {field.type === 'text' && (
                          <Input
                            type="text"
                            value={changes[field.id] !== undefined ? String(changes[field.id]) : String(field.value ?? '')}
                            onChange={(e) => handleChange(field.id, e.target.value)}
                          />
                        )}
                        {field.type === 'textarea' && (
                          <textarea
                            className="w-full px-3 py-2 text-sm rounded-md border border-[var(--border-default)] bg-[var(--surface-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono"
                            style={{ height: '10em' }}
                            value={changes[field.id] !== undefined ? String(changes[field.id]) : String(field.value ?? '')}
                            onChange={(e) => handleChange(field.id, e.target.value)}
                          />
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            </CardBody>
          </Card>
        ))
      )}
    </div>
  )
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, '').replace(/&[^;]+;/g, ' ').trim()
}
