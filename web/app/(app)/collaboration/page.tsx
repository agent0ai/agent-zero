'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Users } from 'lucide-react'

export default function CollaborationPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Collaboration</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">Multi-agent collaboration and cowork sessions</p>
      </div>
      <Card>
        <CardHeader>
          <h2 className="font-semibold text-[var(--text-primary)]">Active Sessions</h2>
        </CardHeader>
        <CardBody>
          <EmptyState
            icon={<Users className="h-10 w-10" />}
            title="No collaboration sessions"
            description="Start a cowork session to collaborate with multiple agents."
          />
        </CardBody>
      </Card>
    </div>
  )
}
