'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { FolderOpen } from 'lucide-react'

export default function FilesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Files</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">Browse and manage agent workspace files</p>
      </div>
      <Card>
        <CardHeader>
          <h2 className="font-semibold text-[var(--text-primary)]">File Browser</h2>
        </CardHeader>
        <CardBody>
          <EmptyState
            icon={<FolderOpen className="h-10 w-10" />}
            title="Connect to backend"
            description="File browser loads from the file_tree API endpoint."
          />
        </CardBody>
      </Card>
    </div>
  )
}
