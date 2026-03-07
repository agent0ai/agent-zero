'use client'

import { Card, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Code, FileText, Download, Trash2 } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { Skill, TrustLevel } from '@/lib/api/endpoints/skills'

const trustVariant: Record<TrustLevel, { variant: 'success' | 'info' | 'warning' | 'neutral'; label: string }> = {
  builtin: { variant: 'success', label: 'Built-in' },
  verified: { variant: 'info', label: 'Verified' },
  community: { variant: 'warning', label: 'Community' },
  local: { variant: 'neutral', label: 'Local' },
}

interface SkillCardProps {
  skill: Skill
  onClick?: () => void
  onToggle?: (enabled: boolean) => void
  onInstall?: () => void
  onUninstall?: () => void
  isToggling?: boolean
  isInstalling?: boolean
}

export function SkillCard({
  skill,
  onClick,
  onToggle,
  onInstall,
  onUninstall,
  isToggling,
  isInstalling,
}: SkillCardProps) {
  const trust = trustVariant[skill.trust_level] ?? trustVariant.local
  const tierLabel = skill.tier === 'python' ? 'Tier 2 Python' : 'Tier 1 Markdown'

  return (
    <Card
      className={cn(
        'hover:border-brand-500/50 transition-colors cursor-pointer',
        !skill.enabled && skill.installed && 'opacity-60',
      )}
      onClick={onClick}
    >
      <CardBody>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            {skill.tier === 'python' ? (
              <Code className="h-4 w-4 text-brand-500 shrink-0" />
            ) : (
              <FileText className="h-4 w-4 text-info shrink-0" />
            )}
            <h3 className="font-medium text-sm text-[var(--text-primary)] truncate">{skill.name}</h3>
          </div>
          <Badge variant={trust.variant} className="text-[10px] shrink-0">
            {trust.label}
          </Badge>
        </div>

        {skill.description && (
          <p className="text-xs text-[var(--text-secondary)] mt-1.5 line-clamp-2">{skill.description}</p>
        )}

        <div className="mt-2 flex items-center gap-2 flex-wrap">
          <Badge variant="neutral" className="text-[10px]">{skill.category}</Badge>
          <Badge variant={skill.tier === 'python' ? 'warning' : 'success'} className="text-[10px]">
            {tierLabel}
          </Badge>
          {skill.version && (
            <span className="text-[10px] text-[var(--text-tertiary)]">v{skill.version}</span>
          )}
        </div>

        {skill.author && (
          <p className="text-[10px] text-[var(--text-tertiary)] mt-1">by {skill.author}</p>
        )}

        <div className="mt-3 flex items-center justify-between gap-2">
          {/* Toggle enabled/disabled */}
          {skill.installed && onToggle && (
            <button
              onClick={(e) => { e.stopPropagation(); onToggle(!skill.enabled) }}
              disabled={isToggling}
              className={cn(
                'relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
                'disabled:cursor-not-allowed disabled:opacity-50',
                skill.enabled ? 'bg-brand-600' : 'bg-slate-300 dark:bg-slate-600',
              )}
            >
              <span
                className={cn(
                  'pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform',
                  skill.enabled ? 'translate-x-4' : 'translate-x-0',
                )}
              />
            </button>
          )}

          {/* Install / Uninstall */}
          <div className="flex gap-1.5 ml-auto">
            {!skill.installed && onInstall && (
              <Button
                size="sm"
                variant="primary"
                onClick={(e) => { e.stopPropagation(); onInstall() }}
                loading={isInstalling}
                className="h-7 px-2 text-xs"
              >
                <Download className="h-3 w-3" />
                Install
              </Button>
            )}
            {skill.installed && onUninstall && (
              <Button
                size="sm"
                variant="ghost"
                onClick={(e) => { e.stopPropagation(); onUninstall() }}
                className="h-7 px-2 text-xs text-danger hover:text-danger-dark"
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>
      </CardBody>
    </Card>
  )
}
