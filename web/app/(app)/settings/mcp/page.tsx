'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Plug } from 'lucide-react'

export default function McpSettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[var(--text-primary)]">MCP Servers</h1>
      <Card>
        <CardHeader><h2 className="font-semibold text-[var(--text-primary)]">Connected Servers</h2></CardHeader>
        <CardBody>
          <EmptyState icon={<Plug className="h-10 w-10" />} title="MCP server management" description="Add and configure Model Context Protocol server connections." />
        </CardBody>
      </Card>
    </div>
  )
}
