'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { StatusDot } from '@/components/ui/StatusDot'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { MessageCircle, Hash, Disc, Phone, Send } from 'lucide-react'
import { useGatewayStatus } from '@/hooks/useMessaging'
import type { LucideIcon } from 'lucide-react'

const CHANNEL_META: Record<string, { icon: LucideIcon; label: string; color: string }> = {
  telegram: { icon: Send, label: 'Telegram', color: 'text-blue-400' },
  slack: { icon: Hash, label: 'Slack', color: 'text-purple-400' },
  discord: { icon: Disc, label: 'Discord', color: 'text-indigo-400' },
  whatsapp: { icon: Phone, label: 'WhatsApp', color: 'text-green-400' },
}

function formatLastActivity(ts: number | null): string {
  if (!ts) return 'No activity'
  const diff = Math.floor((Date.now() / 1000) - ts)
  if (diff < 60) return 'Just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export default function MessagingPage() {
  const { data, isLoading } = useGatewayStatus()
  const channels = data?.channels ?? []

  const connectedCount = channels.filter((c) => c.connected).length
  const totalMessages = channels.reduce((sum, c) => sum + c.message_count, 0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Messaging</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">Multi-channel messaging gateway</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Channels</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">{channels.length}</p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Connected</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">{connectedCount}</p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Total Messages</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">{totalMessages.toLocaleString()}</p>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Channel cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardBody>
                <Skeleton className="h-20 w-full" />
              </CardBody>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {channels.map((ch) => {
            const meta = CHANNEL_META[ch.channel] ?? {
              icon: MessageCircle,
              label: ch.channel,
              color: 'text-[var(--text-tertiary)]',
            }
            const Icon = meta.icon
            const statusType = ch.error ? 'danger' : ch.connected ? 'success' : 'neutral'

            return (
              <Card key={ch.channel} className="hover:border-brand-500/50 transition-colors">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Icon className={`h-5 w-5 ${meta.color}`} />
                      <span className="font-semibold text-[var(--text-primary)]">{meta.label}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <StatusDot status={statusType} pulse={ch.connected && !ch.error} />
                      <Badge variant={statusType}>
                        {ch.error ? 'Error' : ch.connected ? 'Connected' : 'Not Configured'}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardBody>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[var(--text-secondary)]">Messages</span>
                      <span className="text-[var(--text-primary)] font-medium">
                        {ch.message_count.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[var(--text-secondary)]">Last Activity</span>
                      <span className="text-[var(--text-primary)]">
                        {formatLastActivity(ch.last_activity)}
                      </span>
                    </div>
                    {ch.error && (
                      <p className="text-xs text-danger mt-1 truncate" title={ch.error}>
                        {ch.error}
                      </p>
                    )}
                  </div>
                </CardBody>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
