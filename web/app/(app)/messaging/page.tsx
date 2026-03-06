'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { StatusDot } from '@/components/ui/StatusDot'
import { Badge } from '@/components/ui/Badge'
import { MessageCircle } from 'lucide-react'

const channels = [
  { name: 'Telegram', status: 'neutral' as const, description: 'Existing integration via telegram_bridge.py' },
  { name: 'Slack', status: 'neutral' as const, description: 'Planned — requires channel_bridge adapter' },
  { name: 'Discord', status: 'neutral' as const, description: 'Planned — requires channel_bridge adapter' },
  { name: 'WhatsApp', status: 'neutral' as const, description: 'Planned — requires WhatsApp Cloud API' },
]

export default function MessagingPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Messaging</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">Multi-channel messaging gateway</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {channels.map((ch) => (
          <Card key={ch.name}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MessageCircle className="h-4 w-4 text-[var(--text-tertiary)]" />
                  <span className="font-semibold text-[var(--text-primary)]">{ch.name}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <StatusDot status={ch.status} />
                  <Badge variant="neutral">Not Connected</Badge>
                </div>
              </div>
            </CardHeader>
            <CardBody>
              <p className="text-sm text-[var(--text-secondary)]">{ch.description}</p>
            </CardBody>
          </Card>
        ))}
      </div>
    </div>
  )
}
