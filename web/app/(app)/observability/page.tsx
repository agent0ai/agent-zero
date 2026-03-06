'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Eye } from 'lucide-react'

export default function ObservabilityPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Observability</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">Telemetry, logs, and event timeline</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h2 className="font-semibold text-[var(--text-primary)]">Telemetry Timeline</h2>
          </CardHeader>
          <CardBody>
            <EmptyState
              icon={<Eye className="h-10 w-10" />}
              title="No telemetry data"
              description="Telemetry events from telemetry_get will render as a recharts timeline here."
            />
          </CardBody>
        </Card>
        <Card>
          <CardHeader>
            <h2 className="font-semibold text-[var(--text-primary)]">Event Log</h2>
          </CardHeader>
          <CardBody>
            <EmptyState
              icon={<Eye className="h-10 w-10" />}
              title="No events"
              description="Filterable event list from api_log_get."
            />
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
