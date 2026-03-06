'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Settings } from 'lucide-react'

export default function GeneralSettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">General Settings</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">Agent configuration and model preferences</p>
      </div>
      <Card>
        <CardHeader>
          <h2 className="font-semibold text-[var(--text-primary)]">Configuration</h2>
        </CardHeader>
        <CardBody>
          <EmptyState
            icon={<Settings className="h-10 w-10" />}
            title="Settings editor"
            description="Settings form will render from settings_get API with 100+ configuration options."
          />
        </CardBody>
      </Card>
    </div>
  )
}
