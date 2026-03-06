'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Key } from 'lucide-react'

export default function OAuthSettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[var(--text-primary)]">OAuth Integrations</h1>
      <Card>
        <CardHeader><h2 className="font-semibold text-[var(--text-primary)]">Connected Accounts</h2></CardHeader>
        <CardBody>
          <EmptyState icon={<Key className="h-10 w-10" />} title="OAuth integrations" description="Connect Gmail, Google Calendar, and other OAuth2 services." />
        </CardBody>
      </Card>
    </div>
  )
}
