'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { StatusDot } from '@/components/ui/StatusDot'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Key, Mail, Trash2, ExternalLink } from 'lucide-react'
import { useGmailAccounts, useRemoveGmailAccount, useStartGmailOAuth } from '@/hooks/useOAuth'

export default function OAuthSettingsPage() {
  const { data, isLoading } = useGmailAccounts()
  const removeMutation = useRemoveGmailAccount()
  const oauthMutation = useStartGmailOAuth()

  const accounts = data?.accounts ?? {}
  const accountEntries = Object.entries(accounts)

  const handleConnect = (name: string) => {
    oauthMutation.mutate(name, {
      onSuccess: (data) => {
        if (data.auth_url) {
          window.open(data.auth_url, '_blank')
        }
      },
    })
  }

  const handleRemove = (name: string) => {
    if (window.confirm(`Remove Gmail account "${name}"?`)) {
      removeMutation.mutate(name)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">OAuth Integrations</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Manage connected accounts for Gmail, Calendar, and other services
          </p>
        </div>
        <Button
          size="sm"
          onClick={() => {
            const name = window.prompt('Enter account name (e.g., "work", "personal"):')
            if (name?.trim()) handleConnect(name.trim())
          }}
          disabled={oauthMutation.isPending}
        >
          <Mail className="h-4 w-4" />
          Connect Gmail
        </Button>
      </div>

      {/* Gmail Accounts */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Mail className="h-4 w-4 text-brand-500" />
            <h2 className="font-semibold text-[var(--text-primary)]">Gmail Accounts</h2>
            <Badge variant="neutral">{accountEntries.length}</Badge>
          </div>
        </CardHeader>
        <CardBody>
          {isLoading ? (
            <div className="space-y-2">
              {[1, 2].map((i) => <Skeleton key={i} className="h-16 w-full" />)}
            </div>
          ) : accountEntries.length > 0 ? (
            <div className="space-y-3">
              {accountEntries.map(([name, account]) => (
                <div
                  key={name}
                  className="flex items-center justify-between border border-[var(--border-default)] rounded-lg p-3"
                >
                  <div className="flex items-center gap-3">
                    <StatusDot status={account.authenticated ? 'success' : 'danger'} />
                    <div>
                      <p className="text-sm font-medium text-[var(--text-primary)]">{name}</p>
                      <p className="text-xs text-[var(--text-secondary)]">{account.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={account.authenticated ? 'success' : 'danger'}>
                      {account.authenticated ? 'Connected' : 'Disconnected'}
                    </Badge>
                    {!account.authenticated && (
                      <Button size="sm" variant="secondary" onClick={() => handleConnect(name)}>
                        <ExternalLink className="h-3.5 w-3.5" />
                        Re-auth
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleRemove(name)}
                      disabled={removeMutation.isPending}
                    >
                      <Trash2 className="h-3.5 w-3.5 text-danger" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<Key className="h-10 w-10" />}
              title="No accounts connected"
              description="Connect a Gmail account to enable email tools for the agent."
              className="py-8"
            />
          )}
        </CardBody>
      </Card>
    </div>
  )
}
