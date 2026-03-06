'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { StatusDot } from '@/components/ui/StatusDot'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs'
import { GitBranch, Cpu } from 'lucide-react'
import { useLlmRouter, useLlmUsage } from '@/hooks/useLlmRouter'

export default function LlmRouterPage() {
  const { data: routerData, isLoading: routerLoading } = useLlmRouter()
  const { data: usageData, isLoading: usageLoading } = useLlmUsage()

  const models = routerData?.models ?? []
  const usage = usageData?.usage ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">LLM Router</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">Model selection, usage tracking, and routing rules</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Available Models</p>
            {routerLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">{models.length}</p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Total Requests</p>
            {usageLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">
                {usage.reduce((sum, u) => sum + u.requests, 0)}
              </p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Total Cost</p>
            {usageLoading ? (
              <Skeleton className="h-7 w-16 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">
                ${usage.reduce((sum, u) => sum + u.cost, 0).toFixed(2)}
              </p>
            )}
          </CardBody>
        </Card>
      </div>

      <Tabs defaultValue="models">
        <TabsList>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="usage">Usage</TabsTrigger>
        </TabsList>

        <TabsContent value="models">
          <Card>
            <CardHeader>
              <h2 className="font-semibold text-[var(--text-primary)]">Model Dashboard</h2>
            </CardHeader>
            <CardBody className="p-0">
              {routerLoading ? (
                <div className="p-4 space-y-2">
                  {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
                </div>
              ) : models.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Model</TableHead>
                      <TableHead>Provider</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {models.map((model) => (
                      <TableRow key={model.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Cpu className="h-3.5 w-3.5 text-[var(--text-tertiary)]" />
                            <span className="font-medium">{model.name}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="neutral">{model.provider}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1.5">
                            <StatusDot status={model.enabled ? 'success' : 'neutral'} />
                            <span className="text-sm">{model.enabled ? 'Active' : 'Disabled'}</span>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <EmptyState
                  icon={<GitBranch className="h-10 w-10" />}
                  title="No model data"
                  description="Connect to the backend to see available models from llm_router_dashboard."
                  className="py-8"
                />
              )}
            </CardBody>
          </Card>
        </TabsContent>

        <TabsContent value="usage">
          <Card>
            <CardHeader>
              <h2 className="font-semibold text-[var(--text-primary)]">Usage & Costs</h2>
            </CardHeader>
            <CardBody className="p-0">
              {usageLoading ? (
                <div className="p-4 space-y-2">
                  {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
                </div>
              ) : usage.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Model</TableHead>
                      <TableHead>Requests</TableHead>
                      <TableHead>Tokens</TableHead>
                      <TableHead>Cost</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {usage.map((u) => (
                      <TableRow key={u.model}>
                        <TableCell className="font-medium">{u.model}</TableCell>
                        <TableCell>{u.requests.toLocaleString()}</TableCell>
                        <TableCell>{u.tokens.toLocaleString()}</TableCell>
                        <TableCell>${u.cost.toFixed(4)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <EmptyState
                  icon={<GitBranch className="h-10 w-10" />}
                  title="No usage data"
                  description="Token and cost tracking from llm_router_usage will appear here."
                  className="py-8"
                />
              )}
            </CardBody>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
