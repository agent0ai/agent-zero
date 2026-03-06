'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { StatusDot } from '@/components/ui/StatusDot'
import { Skeleton } from '@/components/ui/Skeleton'
import { Button } from '@/components/ui/Button'
import { Activity, Cpu, Rocket, Clock, MessageSquare, Plus, Workflow, Calendar } from 'lucide-react'
import { useHealth } from '@/hooks/useHealth'
import { useRealtime } from '@/hooks/useRealtime'
import Link from 'next/link'

export default function OverviewPage() {
  const health = useHealth()
  const realtime = useRealtime(null, true)

  const contextCount = realtime.contexts?.length ?? 0
  const isHealthy = health.data?.ok ?? false

  const stats = [
    {
      label: 'Active Agents',
      value: realtime.connected ? String(contextCount) : '--',
      icon: Cpu,
      color: 'text-brand-500',
    },
    {
      label: 'System Status',
      value: isHealthy ? 'Healthy' : health.isLoading ? '--' : 'Offline',
      icon: Activity,
      color: isHealthy ? 'text-success' : 'text-danger',
    },
    {
      label: 'Uptime',
      value: health.data?.uptime
        ? `${Math.floor(health.data.uptime / 3600)}h`
        : '--',
      icon: Clock,
      color: 'text-info',
    },
    {
      label: 'Version',
      value: health.data?.version || '1.0.0-beta',
      icon: Rocket,
      color: 'text-warning',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Overview</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          System health and activity summary
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.label}>
              <CardBody>
                <div className="flex items-center gap-3">
                  <div className={stat.color}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-xs text-[var(--text-secondary)]">{stat.label}</p>
                    {health.isLoading ? (
                      <Skeleton className="h-6 w-16 mt-1" />
                    ) : (
                      <p className="text-xl font-semibold text-[var(--text-primary)]">{stat.value}</p>
                    )}
                  </div>
                </div>
              </CardBody>
            </Card>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Health */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-[var(--text-primary)]">System Health</h2>
              <Badge variant={isHealthy ? 'success' : health.isLoading ? 'neutral' : 'danger'}>
                {isHealthy ? 'Operational' : health.isLoading ? 'Checking...' : 'Offline'}
              </Badge>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {[
                { name: 'Flask API', ok: isHealthy },
                { name: 'Agent Runtime', ok: realtime.connected },
                { name: 'Polling Service', ok: realtime.connected },
                { name: 'Task Scheduler', ok: isHealthy },
              ].map((svc) => (
                <div key={svc.name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <StatusDot status={svc.ok ? 'success' : health.isLoading ? 'neutral' : 'danger'} pulse={svc.ok} />
                    <span className="text-[var(--text-primary)]">{svc.name}</span>
                  </div>
                  <span className="text-[var(--text-secondary)]">
                    {svc.ok ? 'Healthy' : health.isLoading ? 'Checking' : 'Unavailable'}
                  </span>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <h2 className="font-semibold text-[var(--text-primary)]">Quick Actions</h2>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-2 gap-3">
              <Link href="/chat">
                <Button variant="secondary" size="sm" className="w-full justify-start">
                  <MessageSquare className="h-4 w-4" /> New Chat
                </Button>
              </Link>
              <Link href="/workflows">
                <Button variant="secondary" size="sm" className="w-full justify-start">
                  <Workflow className="h-4 w-4" /> Workflows
                </Button>
              </Link>
              <Link href="/scheduler">
                <Button variant="secondary" size="sm" className="w-full justify-start">
                  <Calendar className="h-4 w-4" /> Scheduler
                </Button>
              </Link>
              <Link href="/skills">
                <Button variant="secondary" size="sm" className="w-full justify-start">
                  <Plus className="h-4 w-4" /> New Skill
                </Button>
              </Link>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Active Contexts */}
      {realtime.contexts.length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="font-semibold text-[var(--text-primary)]">Active Conversations</h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-2">
              {realtime.contexts.slice(0, 5).map((ctx) => (
                <Link
                  key={ctx.id}
                  href={`/chat/${ctx.id}`}
                  className="flex items-center justify-between rounded-md px-3 py-2 text-sm hover:bg-[var(--surface-secondary)] transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <MessageSquare className="h-3.5 w-3.5 text-[var(--text-tertiary)]" />
                    <span className="text-[var(--text-primary)]">{ctx.name || `Chat ${ctx.id.slice(0, 8)}`}</span>
                  </div>
                  <span className="text-xs text-[var(--text-tertiary)]">{ctx.log_length} messages</span>
                </Link>
              ))}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  )
}
