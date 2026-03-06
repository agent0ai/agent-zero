'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Workflow, Plus } from 'lucide-react'

export default function WorkflowsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Workflows</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">Build and monitor intelligent workflows</p>
        </div>
        <Button size="sm"><Plus className="h-4 w-4" /> New Workflow</Button>
      </div>
      <Card>
        <CardHeader>
          <h2 className="font-semibold text-[var(--text-primary)]">All Workflows</h2>
        </CardHeader>
        <CardBody>
          <EmptyState
            icon={<Workflow className="h-10 w-10" />}
            title="No workflows yet"
            description="Create your first workflow to automate agent tasks. Data loads from workflow_dashboard."
          />
        </CardBody>
      </Card>
    </div>
  )
}
