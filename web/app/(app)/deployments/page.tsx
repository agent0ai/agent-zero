'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Badge } from '@/components/ui/Badge'
import { Rocket } from 'lucide-react'

export default function DeploymentsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Deployments</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">Manage multi-platform deployments</p>
        </div>
        <Badge variant="info">Live</Badge>
      </div>
      <Card>
        <CardHeader>
          <h2 className="font-semibold text-[var(--text-primary)]">Active Deployments</h2>
        </CardHeader>
        <CardBody>
          <EmptyState
            icon={<Rocket className="h-10 w-10" />}
            title="No active deployments"
            description="Deploy your first agent to see it here. Data loads from the telemetry_get endpoint."
          />
        </CardBody>
      </Card>
    </div>
  )
}
