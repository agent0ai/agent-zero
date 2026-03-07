'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { StatusDot } from '@/components/ui/StatusDot'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import {
  MessageCircle,
  Hash,
  Disc,
  Phone,
  Send,
  Mail,
  Globe,
  Radio,
  Webhook,
  Bot,
  Megaphone,
  Rss,
  MessagesSquare,
  Smartphone,
  Headphones,
  Tv,
} from 'lucide-react'
import type { ChannelStatus } from '@/lib/api/endpoints/messaging'
import type { LucideIcon } from 'lucide-react'

const CHANNEL_META: Record<string, { icon: LucideIcon; label: string; color: string }> = {
  telegram: { icon: Send, label: 'Telegram', color: 'text-blue-400' },
  slack: { icon: Hash, label: 'Slack', color: 'text-purple-400' },
  discord: { icon: Disc, label: 'Discord', color: 'text-indigo-400' },
  whatsapp: { icon: Phone, label: 'WhatsApp', color: 'text-green-400' },
  email: { icon: Mail, label: 'Email', color: 'text-amber-400' },
  web: { icon: Globe, label: 'Web Chat', color: 'text-brand-400' },
  radio: { icon: Radio, label: 'Radio', color: 'text-rose-400' },
  webhook: { icon: Webhook, label: 'Webhook', color: 'text-orange-400' },
  bot: { icon: Bot, label: 'Bot API', color: 'text-cyan-400' },
  broadcast: { icon: Megaphone, label: 'Broadcast', color: 'text-pink-400' },
  rss: { icon: Rss, label: 'RSS Feed', color: 'text-yellow-400' },
  forum: { icon: MessagesSquare, label: 'Forum', color: 'text-teal-400' },
  sms: { icon: Smartphone, label: 'SMS', color: 'text-lime-400' },
  voice: { icon: Headphones, label: 'Voice', color: 'text-violet-400' },
  matrix: { icon: Tv, label: 'Matrix', color: 'text-emerald-400' },
  irc: { icon: MessageCircle, label: 'IRC', color: 'text-sky-400' },
}

function formatLastActivity(ts: number | null): string {
  if (!ts) return 'No activity'
  const diff = Math.floor((Date.now() / 1000) - ts)
  if (diff < 60) return 'Just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

interface ChannelCardProps {
  channel: ChannelStatus
  onConnect?: () => void
  onDisconnect?: () => void
  isConnecting?: boolean
}

export function ChannelCard({ channel, onConnect, onDisconnect, isConnecting }: ChannelCardProps) {
  const meta = CHANNEL_META[channel.channel] ?? {
    icon: MessageCircle,
    label: channel.channel,
    color: 'text-[var(--text-tertiary)]',
  }
  const Icon = meta.icon
  const statusType = channel.error ? 'danger' : channel.connected ? 'success' : 'neutral'

  return (
    <Card className="hover:border-brand-500/50 transition-colors">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className={`h-5 w-5 ${meta.color}`} />
            <span className="font-semibold text-[var(--text-primary)]">{meta.label}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <StatusDot status={statusType} pulse={channel.connected && !channel.error} />
            <Badge variant={statusType}>
              {channel.error ? 'Error' : channel.connected ? 'Connected' : 'Not Configured'}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardBody>
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-[var(--text-secondary)]">Messages</span>
            <span className="text-[var(--text-primary)] font-medium">
              {channel.message_count.toLocaleString()}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-[var(--text-secondary)]">Last Activity</span>
            <span className="text-[var(--text-primary)]">
              {formatLastActivity(channel.last_activity)}
            </span>
          </div>
          {channel.error && (
            <p className="text-xs text-danger mt-1 truncate" title={channel.error}>
              {channel.error}
            </p>
          )}
          <div className="pt-2 flex justify-end">
            {channel.connected ? (
              onDisconnect && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={onDisconnect}
                  loading={isConnecting}
                  className="h-7 text-xs"
                >
                  Disconnect
                </Button>
              )
            ) : (
              onConnect && (
                <Button
                  size="sm"
                  variant="primary"
                  onClick={onConnect}
                  loading={isConnecting}
                  className="h-7 text-xs"
                >
                  Connect
                </Button>
              )
            )}
          </div>
        </div>
      </CardBody>
    </Card>
  )
}
