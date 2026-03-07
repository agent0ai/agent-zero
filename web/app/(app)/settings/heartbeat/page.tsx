'use client'

import { useState } from 'react'
import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { StatusDot } from '@/components/ui/StatusDot'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import {
  Heart,
  Play,
  CheckCircle,
  AlertCircle,
  Plus,
  Pencil,
  Trash2,
  Clock,
  Zap,
  Webhook,
  Gauge,
  MessageCircle,
} from 'lucide-react'
import {
  useHeartbeatConfig,
  useHeartbeatLog,
  useUpdateHeartbeat,
  useTriggerHeartbeat,
  useHeartbeatTriggers,
  useCreateHeartbeatTrigger,
  useUpdateHeartbeatTrigger,
  useDeleteHeartbeatTrigger,
} from '@/hooks/useHeartbeat'
import type {
  TriggerType,
  HeartbeatTrigger,
  CreateTriggerInput,
  CronConfig,
  EventConfig,
  WebhookConfig,
  ConditionConfig,
  MessageConfig,
} from '@/lib/api/endpoints/heartbeat'
import { format } from 'date-fns'
import type { LucideIcon } from 'lucide-react'

const TRIGGER_TYPE_META: Record<TriggerType, { icon: LucideIcon; label: string; color: string }> = {
  CRON: { icon: Clock, label: 'Cron Schedule', color: 'text-brand-500' },
  EVENT: { icon: Zap, label: 'Event', color: 'text-warning' },
  WEBHOOK: { icon: Webhook, label: 'Webhook', color: 'text-info' },
  CONDITION: { icon: Gauge, label: 'Condition', color: 'text-danger' },
  MESSAGE: { icon: MessageCircle, label: 'Message', color: 'text-success' },
}

const TRIGGER_TYPES: TriggerType[] = ['CRON', 'EVENT', 'WEBHOOK', 'CONDITION', 'MESSAGE']

function getDefaultConfig(type: TriggerType): CreateTriggerInput['config'] {
  switch (type) {
    case 'CRON': return { expression: '*/30 * * * *', timezone: 'UTC' }
    case 'EVENT': return { event_type: '', filter: {} }
    case 'WEBHOOK': return { url: '', method: 'POST', secret: '' }
    case 'CONDITION': return { metric: '', operator: 'gt' as const, threshold: 0, cooldown_seconds: 300 }
    case 'MESSAGE': return { channel: '', pattern: '' }
  }
}

function formatInterval(seconds: number): string {
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
}

function TriggerForm({
  type,
  config,
  onChange,
}: {
  type: TriggerType
  config: CreateTriggerInput['config']
  onChange: (config: CreateTriggerInput['config']) => void
}) {
  switch (type) {
    case 'CRON': {
      const c = config as CronConfig
      return (
        <div className="space-y-3">
          <Input
            label="Cron Expression"
            value={c.expression}
            onChange={(e) => onChange({ ...c, expression: e.target.value })}
            placeholder="*/30 * * * *"
          />
          <Input
            label="Timezone"
            value={c.timezone}
            onChange={(e) => onChange({ ...c, timezone: e.target.value })}
            placeholder="UTC"
          />
        </div>
      )
    }
    case 'EVENT': {
      const c = config as EventConfig
      return (
        <div className="space-y-3">
          <Input
            label="Event Type"
            value={c.event_type}
            onChange={(e) => onChange({ ...c, event_type: e.target.value })}
            placeholder="deployment.completed"
          />
        </div>
      )
    }
    case 'WEBHOOK': {
      const c = config as WebhookConfig
      return (
        <div className="space-y-3">
          <Input
            label="URL"
            value={c.url}
            onChange={(e) => onChange({ ...c, url: e.target.value })}
            placeholder="https://example.com/webhook"
          />
          <Input
            label="Method"
            value={c.method}
            onChange={(e) => onChange({ ...c, method: e.target.value })}
            placeholder="POST"
          />
          <Input
            label="Secret"
            value={c.secret}
            onChange={(e) => onChange({ ...c, secret: e.target.value })}
            placeholder="webhook-secret"
            type="password"
          />
        </div>
      )
    }
    case 'CONDITION': {
      const c = config as ConditionConfig
      return (
        <div className="space-y-3">
          <Input
            label="Metric"
            value={c.metric}
            onChange={(e) => onChange({ ...c, metric: e.target.value })}
            placeholder="cpu_usage"
          />
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-[var(--text-primary)]">Operator</label>
              <select
                value={c.operator}
                onChange={(e) => onChange({ ...c, operator: e.target.value as ConditionConfig['operator'] })}
                className="flex h-9 w-full rounded-md border bg-[var(--surface-primary)] px-3 py-1 text-sm border-[var(--border-default)] text-[var(--text-primary)]"
              >
                <option value="gt">&gt; Greater than</option>
                <option value="gte">&gt;= Greater or equal</option>
                <option value="lt">&lt; Less than</option>
                <option value="lte">&lt;= Less or equal</option>
                <option value="eq">= Equal</option>
              </select>
            </div>
            <Input
              label="Threshold"
              type="number"
              value={String(c.threshold)}
              onChange={(e) => onChange({ ...c, threshold: parseFloat(e.target.value) || 0 })}
            />
          </div>
          <Input
            label="Cooldown (seconds)"
            type="number"
            value={String(c.cooldown_seconds)}
            onChange={(e) => onChange({ ...c, cooldown_seconds: parseInt(e.target.value, 10) || 300 })}
          />
        </div>
      )
    }
    case 'MESSAGE': {
      const c = config as MessageConfig
      return (
        <div className="space-y-3">
          <Input
            label="Channel"
            value={c.channel}
            onChange={(e) => onChange({ ...c, channel: e.target.value })}
            placeholder="telegram"
          />
          <Input
            label="Pattern (regex)"
            value={c.pattern}
            onChange={(e) => onChange({ ...c, pattern: e.target.value })}
            placeholder="^!heartbeat"
          />
        </div>
      )
    }
  }
}

export default function HeartbeatSettingsPage() {
  const { data: config, isLoading: configLoading } = useHeartbeatConfig()
  const { data: logData, isLoading: logLoading } = useHeartbeatLog()
  const { data: triggers, isLoading: triggersLoading } = useHeartbeatTriggers()
  const updateMutation = useUpdateHeartbeat()
  const triggerMutation = useTriggerHeartbeat()
  const createTriggerMutation = useCreateHeartbeatTrigger()
  const updateTriggerMutation = useUpdateHeartbeatTrigger()
  const deleteTriggerMutation = useDeleteHeartbeatTrigger()

  const [editInterval, setEditInterval] = useState<string>('')
  const [triggerModalOpen, setTriggerModalOpen] = useState(false)
  const [editingTrigger, setEditingTrigger] = useState<HeartbeatTrigger | null>(null)
  const [triggerName, setTriggerName] = useState('')
  const [triggerType, setTriggerType] = useState<TriggerType>('CRON')
  const [triggerConfig, setTriggerConfig] = useState<CreateTriggerInput['config']>(getDefaultConfig('CRON'))

  const openCreateTrigger = () => {
    setEditingTrigger(null)
    setTriggerName('')
    setTriggerType('CRON')
    setTriggerConfig(getDefaultConfig('CRON'))
    setTriggerModalOpen(true)
  }

  const openEditTrigger = (trigger: HeartbeatTrigger) => {
    setEditingTrigger(trigger)
    setTriggerName(trigger.name)
    setTriggerType(trigger.type)
    setTriggerConfig(trigger.config)
    setTriggerModalOpen(true)
  }

  const handleSaveTrigger = () => {
    if (!triggerName.trim()) return
    if (editingTrigger) {
      updateTriggerMutation.mutate(
        { id: editingTrigger.id, name: triggerName, type: triggerType, config: triggerConfig, enabled: editingTrigger.enabled },
        { onSuccess: () => setTriggerModalOpen(false) },
      )
    } else {
      createTriggerMutation.mutate(
        { name: triggerName, type: triggerType, enabled: true, config: triggerConfig },
        { onSuccess: () => setTriggerModalOpen(false) },
      )
    }
  }

  const handleDeleteTrigger = (id: string) => {
    deleteTriggerMutation.mutate(id)
  }

  const handleToggleTriggerEnabled = (trigger: HeartbeatTrigger) => {
    updateTriggerMutation.mutate({ id: trigger.id, enabled: !trigger.enabled })
  }

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

      {/* Triggers */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-[var(--text-primary)]">Triggers</h2>
            <Button size="sm" onClick={openCreateTrigger}>
              <Plus className="h-3.5 w-3.5" />
              Add Trigger
            </Button>
          </div>
        </CardHeader>
        <CardBody>
          {triggersLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : triggers && triggers.length > 0 ? (
            <div className="space-y-3">
              {triggers.map((trigger) => {
                const meta = TRIGGER_TYPE_META[trigger.type]
                const TriggerIcon = meta.icon
                return (
                  <div
                    key={trigger.id}
                    className="border border-[var(--border-default)] rounded-lg p-3 flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <TriggerIcon className={`h-5 w-5 shrink-0 ${meta.color}`} />
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm text-[var(--text-primary)] truncate">
                            {trigger.name}
                          </span>
                          <Badge variant="neutral" className="text-[10px]">{meta.label}</Badge>
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                          <Badge variant={trigger.enabled ? 'success' : 'neutral'} className="text-[10px]">
                            {trigger.enabled ? 'Active' : 'Inactive'}
                          </Badge>
                          {trigger.last_fired && (
                            <span className="text-[10px] text-[var(--text-tertiary)]">
                              Last: {format(new Date(trigger.last_fired), 'MMM d, HH:mm')}
                            </span>
                          )}
                          <span className="text-[10px] text-[var(--text-tertiary)]">
                            Fired {trigger.fire_count}x
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <button
                        onClick={() => handleToggleTriggerEnabled(trigger)}
                        disabled={updateTriggerMutation.isPending}
                        className="p-1.5 rounded-md text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-tertiary)]"
                        title={trigger.enabled ? 'Disable' : 'Enable'}
                      >
                        <StatusDot status={trigger.enabled ? 'success' : 'neutral'} />
                      </button>
                      <button
                        onClick={() => openEditTrigger(trigger)}
                        className="p-1.5 rounded-md text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-tertiary)]"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteTrigger(trigger.id)}
                        disabled={deleteTriggerMutation.isPending}
                        className="p-1.5 rounded-md text-[var(--text-tertiary)] hover:text-danger hover:bg-[var(--surface-tertiary)]"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <EmptyState
              icon={<Zap className="h-10 w-10" />}
              title="No triggers configured"
              description="Add triggers to fire heartbeat on schedules, events, webhooks, conditions, or messages."
              action={
                <Button size="sm" onClick={openCreateTrigger}>
                  <Plus className="h-3.5 w-3.5" />
                  Create First Trigger
                </Button>
              }
              className="py-8"
            />
          )}
        </CardBody>
      </Card>

      {/* Trigger Create/Edit Modal */}
      <Modal
        open={triggerModalOpen}
        onOpenChange={setTriggerModalOpen}
        title={editingTrigger ? 'Edit Trigger' : 'Create Trigger'}
        description="Configure when the heartbeat daemon should fire."
      >
        <div className="space-y-4">
          <Input
            label="Trigger Name"
            value={triggerName}
            onChange={(e) => setTriggerName(e.target.value)}
            placeholder="My trigger"
          />

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-[var(--text-primary)]">Trigger Type</label>
            <div className="grid grid-cols-5 gap-1.5">
              {TRIGGER_TYPES.map((t) => {
                const m = TRIGGER_TYPE_META[t]
                const Icon = m.icon
                return (
                  <button
                    key={t}
                    onClick={() => {
                      setTriggerType(t)
                      setTriggerConfig(getDefaultConfig(t))
                    }}
                    className={`flex flex-col items-center gap-1 p-2 rounded-md text-xs transition-colors ${
                      triggerType === t
                        ? 'bg-brand-500 text-white'
                        : 'bg-[var(--surface-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {t}
                  </button>
                )
              })}
            </div>
          </div>

          <TriggerForm type={triggerType} config={triggerConfig} onChange={setTriggerConfig} />

          <div className="flex justify-end gap-2 pt-2">
            <Button size="sm" variant="secondary" onClick={() => setTriggerModalOpen(false)}>
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleSaveTrigger}
              loading={createTriggerMutation.isPending || updateTriggerMutation.isPending}
              disabled={!triggerName.trim()}
            >
              {editingTrigger ? 'Update' : 'Create'}
            </Button>
          </div>
        </div>
      </Modal>

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
