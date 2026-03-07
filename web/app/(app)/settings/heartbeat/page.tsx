'use client'

import { useState } from 'react'
import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { StatusDot } from '@/components/ui/StatusDot'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Heart, Play, CheckCircle, AlertCircle } from 'lucide-react'
import {
  useHeartbeatConfig,
  useHeartbeatLog,
  useUpdateHeartbeat,
  useTriggerHeartbeat,
} from '@/hooks/useHeartbeat'
import { format } from 'date-fns'

function formatInterval(seconds: number): string {
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
}

export default function HeartbeatSettingsPage() {
  const { data: config, isLoading: configLoading } = useHeartbeatConfig()
  const { data: logData, isLoading: logLoading } = useHeartbeatLog()
  const updateMutation = useUpdateHeartbeat()
  const triggerMutation = useTriggerHeartbeat()

  const [editInterval, setEditInterval] = useState<string>('')

  const log = logData?.log ?? []

  const handleToggle = () => {
    if (!config) return
    updateMutation.mutate({ enabled: !config.enabled })
  }

  const handleIntervalUpdate = () => {
    const seconds = parseInt(editInterval, 10)
    if (isNaN(seconds) || seconds < 60) return
    updateMutation.mutate({ interval_seconds: seconds })
    setEditInterval('')
  }

  const handleTrigger = () => {
    triggerMutation.mutate()
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Heartbeat</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          Proactive agent daemon — executes HEARTBEAT.md checklist at regular intervals
        </p>
      </div>

      {/* Status + Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Status</p>
            {configLoading ? (
              <Skeleton className="h-7 w-20 mt-1" />
            ) : (
              <div className="flex items-center gap-2 mt-1">
                <StatusDot
                  status={config?.running ? 'success' : config?.enabled ? 'warning' : 'neutral'}
                  pulse={config?.running}
                />
                <span className="text-sm font-medium text-[var(--text-primary)]">
                  {config?.running ? 'Running' : config?.enabled ? 'Enabled (idle)' : 'Disabled'}
                </span>
              </div>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Interval</p>
            {configLoading ? (
              <Skeleton className="h-7 w-16 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">
                {formatInterval(config?.interval_seconds ?? 1800)}
              </p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Total Runs</p>
            {configLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">{config?.run_count ?? 0}</p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Last Run</p>
            {configLoading ? (
              <Skeleton className="h-7 w-24 mt-1" />
            ) : (
              <p className="text-sm font-medium text-[var(--text-primary)] mt-1">
                {config?.last_run
                  ? format(new Date(config.last_run), 'MMM d, HH:mm')
                  : 'Never'}
              </p>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <h2 className="font-semibold text-[var(--text-primary)]">Controls</h2>
        </CardHeader>
        <CardBody>
          <div className="flex flex-wrap gap-3 items-center">
            <Button
              size="sm"
              variant={config?.enabled ? 'danger' : 'primary'}
              onClick={handleToggle}
              disabled={configLoading || updateMutation.isPending}
            >
              {config?.enabled ? 'Disable' : 'Enable'} Heartbeat
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={handleTrigger}
              disabled={triggerMutation.isPending}
            >
              <Play className="h-3.5 w-3.5" />
              {triggerMutation.isPending ? 'Running...' : 'Run Now'}
            </Button>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min={60}
                max={86400}
                placeholder="Seconds"
                value={editInterval}
                onChange={(e) => setEditInterval(e.target.value)}
                className="w-24 px-2 py-1 text-sm rounded-md border border-[var(--border-default)] bg-[var(--surface-primary)] text-[var(--text-primary)]"
              />
              <Button
                size="sm"
                variant="secondary"
                onClick={handleIntervalUpdate}
                disabled={!editInterval || updateMutation.isPending}
              >
                Set Interval
              </Button>
            </div>
          </div>
          <p className="text-xs text-[var(--text-tertiary)] mt-2">
            Checklist path: <code className="font-mono">{config?.heartbeat_path ?? 'HEARTBEAT.md'}</code>
          </p>
        </CardBody>
      </Card>

      {/* Activity Log */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-[var(--text-primary)]">Activity Log</h2>
            <Badge variant="neutral">{log.length} runs</Badge>
          </div>
        </CardHeader>
        <CardBody>
          {logLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-16 w-full" />)}
            </div>
          ) : log.length > 0 ? (
            <div className="space-y-3">
              {log.slice().reverse().slice(0, 20).map((run) => (
                <div
                  key={run.run_id}
                  className="border border-[var(--border-default)] rounded-lg p-3"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          run.status === 'completed' ? 'success'
                          : run.status === 'error' ? 'danger'
                          : 'info'
                        }
                      >
                        {run.status}
                      </Badge>
                      <span className="text-xs text-[var(--text-tertiary)]">
                        {run.started_at
                          ? format(new Date(run.started_at), 'MMM d, HH:mm:ss')
                          : ''}
                      </span>
                    </div>
                    <span className="text-xs text-[var(--text-tertiary)]">
                      {run.items.length} items
                    </span>
                  </div>
                  {run.error && (
                    <p className="text-xs text-danger mb-2">{run.error}</p>
                  )}
                  <div className="space-y-1">
                    {run.items.map((item, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm">
                        {item.completed ? (
                          <CheckCircle className="h-3.5 w-3.5 text-success mt-0.5 shrink-0" />
                        ) : (
                          <AlertCircle className="h-3.5 w-3.5 text-[var(--text-tertiary)] mt-0.5 shrink-0" />
                        )}
                        <div className="min-w-0">
                          <span className="text-[var(--text-primary)]">{item.text}</span>
                          {item.result && (
                            <p className="text-xs text-[var(--text-secondary)] mt-0.5 truncate">
                              {item.result}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<Heart className="h-10 w-10" />}
              title="No heartbeat runs yet"
              description="Enable the heartbeat daemon or click 'Run Now' to execute HEARTBEAT.md."
              className="py-8"
            />
          )}
        </CardBody>
      </Card>
    </div>
  )
}
