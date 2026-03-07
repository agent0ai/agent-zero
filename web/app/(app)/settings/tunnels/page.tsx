'use client'

import { useState } from 'react'
import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { StatusDot } from '@/components/ui/StatusDot'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Globe, Save, ExternalLink } from 'lucide-react'
import { useTunnelSettings, useSaveTunnelSettings } from '@/hooks/useTunnels'

export default function TunnelSettingsPage() {
  const { data, isLoading } = useTunnelSettings()
  const saveMutation = useSaveTunnelSettings()
  const [editProvider, setEditProvider] = useState('')
  const [editInterval, setEditInterval] = useState('')

  const settings = data?.settings
  const watchdog = data?.watchdog

  const handleSave = () => {
    const updates: Record<string, unknown> = {}
    if (editProvider) updates.provider = editProvider
    if (editInterval) updates.watchdog_interval = parseInt(editInterval, 10)
    if (Object.keys(updates).length > 0) {
      saveMutation.mutate(updates, {
        onSuccess: () => {
          setEditProvider('')
          setEditInterval('')
        },
      })
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Tunnels</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          Configure tunnels for external webhook access and remote connections
        </p>
      </div>

      {/* Status */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Watchdog Status</p>
            {isLoading ? (
              <Skeleton className="h-7 w-20 mt-1" />
            ) : (
              <div className="flex items-center gap-2 mt-1">
                <StatusDot
                  status={watchdog?.running ? 'success' : 'neutral'}
                  pulse={watchdog?.running}
                />
                <span className="text-sm font-medium text-[var(--text-primary)]">
                  {watchdog?.running ? 'Running' : 'Stopped'}
                </span>
              </div>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Provider</p>
            {isLoading ? (
              <Skeleton className="h-7 w-24 mt-1" />
            ) : (
              <p className="text-lg font-semibold text-[var(--text-primary)] mt-1">
                {settings?.provider ?? 'cloudflared'}
              </p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Tunnel URL</p>
            {isLoading ? (
              <Skeleton className="h-7 w-32 mt-1" />
            ) : watchdog?.url ? (
              <div className="flex items-center gap-1 mt-1">
                <a
                  href={watchdog.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-brand-500 hover:underline truncate"
                >
                  {watchdog.url}
                </a>
                <ExternalLink className="h-3 w-3 text-brand-500 shrink-0" />
              </div>
            ) : (
              <p className="text-sm text-[var(--text-tertiary)] mt-1">Not available</p>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Configuration */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Globe className="h-4 w-4 text-brand-500" />
            <h2 className="font-semibold text-[var(--text-primary)]">Configuration</h2>
          </div>
        </CardHeader>
        <CardBody>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 items-start">
              <div>
                <p className="text-sm font-medium text-[var(--text-primary)]">Provider</p>
                <p className="text-xs text-[var(--text-secondary)]">Tunnel provider (e.g., cloudflared, ngrok)</p>
              </div>
              <div className="md:col-span-2">
                <Input
                  type="text"
                  value={editProvider || settings?.provider || ''}
                  onChange={(e) => setEditProvider(e.target.value)}
                  placeholder="cloudflared"
                />
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 items-start">
              <div>
                <p className="text-sm font-medium text-[var(--text-primary)]">Watchdog Interval</p>
                <p className="text-xs text-[var(--text-secondary)]">Health check interval in seconds (min: 15)</p>
              </div>
              <div className="md:col-span-2">
                <Input
                  type="number"
                  min={15}
                  value={editInterval || String(settings?.watchdog_interval ?? 60)}
                  onChange={(e) => setEditInterval(e.target.value)}
                />
              </div>
            </div>
            <div className="flex justify-end">
              <Button
                size="sm"
                onClick={handleSave}
                disabled={saveMutation.isPending || (!editProvider && !editInterval)}
              >
                <Save className="h-3.5 w-3.5" />
                {saveMutation.isPending ? 'Saving...' : 'Save'}
              </Button>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Error display */}
      {watchdog?.error && (
        <Card>
          <CardBody>
            <div className="flex items-start gap-2">
              <Badge variant="danger">Error</Badge>
              <p className="text-sm text-danger">{watchdog.error}</p>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  )
}
