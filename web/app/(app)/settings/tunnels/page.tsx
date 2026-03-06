'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Globe } from 'lucide-react'

export default function TunnelSettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[var(--text-primary)]">Tunnels</h1>
      <Card>
        <CardHeader><h2 className="font-semibold text-[var(--text-primary)]">Tunnel Configuration</h2></CardHeader>
        <CardBody>
          <EmptyState icon={<Globe className="h-10 w-10" />} title="Tunnel settings" description="Configure tunnels for external webhook access and remote connections." />
        </CardBody>
      </Card>
    </div>
  )
}
