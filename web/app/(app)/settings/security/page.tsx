'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Shield } from 'lucide-react'

export default function SecuritySettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[var(--text-primary)]">Security</h1>
      <Card>
        <CardHeader><h2 className="font-semibold text-[var(--text-primary)]">Authentication & Keys</h2></CardHeader>
        <CardBody>
          <EmptyState icon={<Shield className="h-10 w-10" />} title="Security settings" description="Passkey auth, API keys, and audit log configuration." />
        </CardBody>
      </Card>
    </div>
  )
}
