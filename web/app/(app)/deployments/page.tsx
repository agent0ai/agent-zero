'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { StatusDot } from '@/components/ui/StatusDot'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { Rocket, Activity, Clock } from 'lucide-react'
import { useTelemetry } from '@/hooks/useTelemetry'
import { useHealth } from '@/hooks/useHealth'
import { format } from 'date-fns'

export default function DeploymentsPage() {
  const { data: telemetryData, isLoading: telemetryLoading } = useTelemetry()
  const { data: healthData, isLoading: healthLoading } = useHealth()

  const events = telemetryData?.events ?? []
  const deploymentEvents = events.filter(
    (e) => e.type === 'deployment' || e.type === 'deploy' || e.type?.includes('deploy')
  )
  const isLoading = telemetryLoading || healthLoading

  const systemStatus = healthData?.status ?? 'unknown'
  const uptime = healthData?.uptime ?? null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Deployments</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">System status and deployment telemetry</p>
        </div>
        <Badge variant={systemStatus === 'ok' ? 'success' : systemStatus === 'degraded' ? 'warning' : 'info'}>
          {systemStatus === 'ok' ? 'Healthy' : systemStatus}
        </Badge>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">System Status</p>
            {isLoading ? (
              <Skeleton className="h-7 w-20 mt-1" />
            ) : (
              <div className="flex items-center gap-2 mt-1">
                <StatusDot
                  status={systemStatus === 'ok' ? 'success' : systemStatus === 'degraded' ? 'warning' : 'neutral'}
                  pulse={systemStatus === 'ok'}
                />
                <span className="text-sm font-medium text-[var(--text-primary)]">
                  {systemStatus === 'ok' ? 'All Systems Operational' : systemStatus}
                </span>
              </div>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Uptime</p>
            {isLoading ? (
              <Skeleton className="h-7 w-16 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">
                {uptime ? formatUptime(uptime) : '—'}
              </p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Telemetry Events</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">{events.length}</p>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Deployment Events */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-[var(--text-primary)]">Deployment Events</h2>
            <Badge variant="neutral">{deploymentEvents.length} events</Badge>
          </div>
        </CardHeader>
        <CardBody className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-2">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : deploymentEvents.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {deploymentEvents.slice().reverse().slice(0, 50).map((event, i) => (
                  <TableRow key={i}>
                    <TableCell>
                      <div className="flex items-center gap-1 text-xs text-[var(--text-secondary)]">
                        <Clock className="h-3 w-3" />
                        {event.timestamp
                          ? format(new Date(event.timestamp), 'MMM d, HH:mm:ss')
                          : '—'}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="info">{event.type}</Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-[var(--text-secondary)] truncate block max-w-md">
                        {summarizeEventData(event.data)}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <EmptyState
              icon={<Rocket className="h-10 w-10" />}
              title="No deployment events"
              description="Deployment telemetry events will appear here as they occur."
              className="py-8"
            />
          )}
        </CardBody>
      </Card>

      {/* Recent Telemetry */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-[var(--text-primary)]">Recent Telemetry</h2>
            <Badge variant="neutral">{events.length} total</Badge>
          </div>
        </CardHeader>
        <CardBody className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-2">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : events.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {events.slice().reverse().slice(0, 30).map((event, i) => (
                  <TableRow key={i}>
                    <TableCell>
                      <div className="flex items-center gap-1 text-xs text-[var(--text-secondary)]">
                        <Clock className="h-3 w-3" />
                        {event.timestamp
                          ? format(new Date(event.timestamp), 'MMM d, HH:mm:ss')
                          : '—'}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          event.type?.includes('error') ? 'danger'
                          : event.type?.includes('deploy') ? 'success'
                          : 'neutral'
                        }
                      >
                        {event.type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-[var(--text-secondary)] truncate block max-w-md">
                        {summarizeEventData(event.data)}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <EmptyState
              icon={<Activity className="h-10 w-10" />}
              title="No telemetry yet"
              description="Enable telemetry in settings to track system events."
              className="py-8"
            />
          )}
        </CardBody>
      </Card>
    </div>
  )
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  if (days > 0) return `${days}d ${hours}h`
  if (hours > 0) return `${hours}h ${mins}m`
  return `${mins}m`
}

function summarizeEventData(data: Record<string, unknown>): string {
  if (!data || typeof data !== 'object') return ''
  const parts: string[] = []
  for (const [key, val] of Object.entries(data)) {
    if (val !== null && val !== undefined && val !== '') {
      parts.push(`${key}: ${typeof val === 'object' ? JSON.stringify(val) : String(val)}`)
    }
  }
  return parts.join(', ') || '—'
}
