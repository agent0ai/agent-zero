'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Archive, Plus } from 'lucide-react'

export default function BackupsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Backups</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">Create and restore system backups</p>
        </div>
        <Button size="sm"><Plus className="h-4 w-4" /> Create Backup</Button>
      </div>
      <Card>
        <CardHeader>
          <h2 className="font-semibold text-[var(--text-primary)]">Backup History</h2>
        </CardHeader>
        <CardBody>
          <EmptyState
            icon={<Archive className="h-10 w-10" />}
            title="No backups"
            description="Create your first backup. Data loads from backup_list."
          />
        </CardBody>
      </Card>
    </div>
  )
}
