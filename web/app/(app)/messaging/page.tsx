'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardBody } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { useGatewayStatus } from '@/hooks/useMessaging'
import { ChannelCard } from '@/components/messaging/ChannelCard'
import { connectChannel, disconnectChannel, type ChannelStatus } from '@/lib/api/endpoints/messaging'

/** Default channel list for when no backend channels are returned */
const DEFAULT_CHANNELS: ChannelStatus[] = [
  { channel: 'telegram', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
  { channel: 'slack', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
  { channel: 'discord', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
  { channel: 'whatsapp', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
  { channel: 'email', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
  { channel: 'web', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
  { channel: 'webhook', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
  { channel: 'bot', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
  { channel: 'broadcast', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
  { channel: 'rss', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
  { channel: 'forum', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
  { channel: 'sms', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
  { channel: 'voice', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
  { channel: 'matrix', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
  { channel: 'irc', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
  { channel: 'radio', connected: false, enabled: false, error: null, last_activity: null, message_count: 0 },
]

export default function MessagingPage() {
  const { data, isLoading } = useGatewayStatus()
  const qc = useQueryClient()

  const channels = data?.channels && data.channels.length > 0 ? data.channels : DEFAULT_CHANNELS

  const connectMutation = useMutation({
    mutationFn: (channel: string) => connectChannel(channel),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gateway-status'] }),
  })

  const disconnectMutation = useMutation({
    mutationFn: (channel: string) => disconnectChannel(channel),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gateway-status'] }),
  })

  const connectedCount = channels.filter((c) => c.connected).length
  const totalMessages = channels.reduce((sum, c) => sum + c.message_count, 0)
  const errorCount = channels.filter((c) => c.error).length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Messaging</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">Multi-channel messaging gateway</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
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
              <p className="text-2xl font-semibold text-success">{connectedCount}</p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Errors</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className={`text-2xl font-semibold ${errorCount > 0 ? 'text-danger' : 'text-[var(--text-primary)]'}`}>
                {errorCount}
              </p>
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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Card key={i}>
              <CardBody>
                <Skeleton className="h-28 w-full" />
              </CardBody>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {channels.map((ch) => (
            <ChannelCard
              key={ch.channel}
              channel={ch}
              onConnect={() => connectMutation.mutate(ch.channel)}
              onDisconnect={() => disconnectMutation.mutate(ch.channel)}
              isConnecting={connectMutation.isPending || disconnectMutation.isPending}
            />
          ))}
        </div>
      )}
    </div>
  )
}
