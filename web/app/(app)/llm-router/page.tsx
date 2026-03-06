'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { GitBranch } from 'lucide-react'

export default function LlmRouterPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">LLM Router</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">Model selection, usage tracking, and routing rules</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h2 className="font-semibold text-[var(--text-primary)]">Model Dashboard</h2>
          </CardHeader>
          <CardBody>
            <EmptyState
              icon={<GitBranch className="h-10 w-10" />}
              title="No model data"
              description="Model list and usage stats from llm_router_dashboard."
            />
          </CardBody>
        </Card>
        <Card>
          <CardHeader>
            <h2 className="font-semibold text-[var(--text-primary)]">Usage & Costs</h2>
          </CardHeader>
          <CardBody>
            <EmptyState
              icon={<GitBranch className="h-10 w-10" />}
              title="No usage data"
              description="Token and cost tracking from llm_router_usage."
            />
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
