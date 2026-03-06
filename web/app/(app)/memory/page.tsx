'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Brain } from 'lucide-react'

export default function MemoryPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Memory</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">Agent memory and knowledge management</p>
      </div>
      <Card>
        <CardHeader>
          <h2 className="font-semibold text-[var(--text-primary)]">Memory Store</h2>
        </CardHeader>
        <CardBody>
          <EmptyState
            icon={<Brain className="h-10 w-10" />}
            title="Memory dashboard"
            description="View and manage FAISS embeddings and in-context memories. Data loads from memory_dashboard."
          />
        </CardBody>
      </Card>
    </div>
  )
}
