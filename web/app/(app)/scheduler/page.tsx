'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Calendar, Plus } from 'lucide-react'

export default function SchedulerPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Scheduler</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">Schedule recurring agent tasks with cron expressions</p>
        </div>
        <Button size="sm"><Plus className="h-4 w-4" /> New Task</Button>
      </div>
      <Card>
        <CardHeader>
          <h2 className="font-semibold text-[var(--text-primary)]">Scheduled Tasks</h2>
        </CardHeader>
        <CardBody>
          <EmptyState
            icon={<Calendar className="h-10 w-10" />}
            title="No scheduled tasks"
            description="Create a scheduled task to run agents on a cron schedule. Data loads from scheduler_tasks_list."
          />
        </CardBody>
      </Card>
    </div>
  )
}
