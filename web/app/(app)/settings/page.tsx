'use client'

import Link from 'next/link'
import { Card, CardBody } from '@/components/ui/Card'
import { Settings, Shield, Plug, Key, Globe, Heart } from 'lucide-react'

const sections = [
  { label: 'General', href: '/settings/general', icon: Settings, description: 'Agent configuration, model settings, preferences' },
  { label: 'Security', href: '/settings/security', icon: Shield, description: 'Authentication, API keys, audit logs' },
  { label: 'Heartbeat', href: '/settings/heartbeat', icon: Heart, description: 'Proactive daemon — auto-execute HEARTBEAT.md checklist' },
  { label: 'MCP Servers', href: '/settings/mcp', icon: Plug, description: 'Model Context Protocol server connections' },
  { label: 'OAuth', href: '/settings/oauth', icon: Key, description: 'OAuth2 integrations (Gmail, Calendar, etc.)' },
  { label: 'Tunnels', href: '/settings/tunnels', icon: Globe, description: 'Tunnel configuration for external access' },
]

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Settings</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">Configure Agent Jumbo</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {sections.map((s) => {
          const Icon = s.icon
          return (
            <Link key={s.href} href={s.href}>
              <Card className="hover:border-brand-500 transition-colors h-full">
                <CardBody>
                  <Icon className="h-5 w-5 text-brand-500 mb-2" />
                  <h3 className="font-semibold text-[var(--text-primary)]">{s.label}</h3>
                  <p className="text-sm text-[var(--text-secondary)] mt-1">{s.description}</p>
                </CardBody>
              </Card>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
