'use client'

import { Modal } from '@/components/ui/Modal'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import {
  Code,
  FileText,
  Shield,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  Download,
  Trash2,
  Zap,
} from 'lucide-react'
import { cn } from '@/lib/cn'
import { useSkill, useInstallSkill, useUninstallSkill, useToggleSkill, useScanSkill } from '@/hooks/useSkills'
import type { TrustLevel, ScanResult } from '@/lib/api/endpoints/skills'
import { useState } from 'react'

const trustMeta: Record<TrustLevel, { variant: 'success' | 'info' | 'warning' | 'neutral'; label: string; icon: typeof Shield }> = {
  builtin: { variant: 'success', label: 'Built-in', icon: ShieldCheck },
  verified: { variant: 'info', label: 'Verified', icon: ShieldCheck },
  community: { variant: 'warning', label: 'Community', icon: Shield },
  local: { variant: 'neutral', label: 'Local', icon: ShieldAlert },
}

const severityVariant: Record<string, 'danger' | 'warning' | 'info' | 'neutral'> = {
  critical: 'danger',
  high: 'danger',
  medium: 'warning',
  low: 'neutral',
}

interface SkillDetailProps {
  skillName: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SkillDetail({ skillName, open, onOpenChange }: SkillDetailProps) {
  const { data: skill, isLoading } = useSkill(skillName)
  const installMutation = useInstallSkill()
  const uninstallMutation = useUninstallSkill()
  const toggleMutation = useToggleSkill()
  const scanMutation = useScanSkill()
  const [scanResult, setScanResult] = useState<ScanResult | null>(null)

  const handleScan = async () => {
    if (!skillName) return
    const result = await scanMutation.mutateAsync(skillName)
    setScanResult(result)
  }

  const handleInstall = () => {
    if (!skillName) return
    installMutation.mutate(skillName)
  }

  const handleUninstall = () => {
    if (!skillName) return
    uninstallMutation.mutate(skillName)
  }

  const handleToggle = () => {
    if (!skill) return
    toggleMutation.mutate({ name: skill.name, enabled: !skill.enabled })
  }

  const trust = skill ? (trustMeta[skill.trust_level] ?? trustMeta.local) : trustMeta.local
  const TrustIcon = trust.icon

  return (
    <Modal
      open={open}
      onOpenChange={(v) => { onOpenChange(v); if (!v) setScanResult(null) }}
      title={skill?.name ?? 'Skill Details'}
      description={skill?.description}
      className="max-w-xl"
    >
      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : skill ? (
        <div className="space-y-4">
          {/* Metadata */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-[var(--text-secondary)]">Version</span>
              <p className="text-[var(--text-primary)] font-medium">{skill.version || 'N/A'}</p>
            </div>
            <div>
              <span className="text-[var(--text-secondary)]">Author</span>
              <p className="text-[var(--text-primary)] font-medium">{skill.author || 'Unknown'}</p>
            </div>
            <div>
              <span className="text-[var(--text-secondary)]">Category</span>
              <p className="text-[var(--text-primary)] font-medium">{skill.category}</p>
            </div>
            <div>
              <span className="text-[var(--text-secondary)]">Source</span>
              <p className="text-[var(--text-primary)] font-medium capitalize">{skill.source}</p>
            </div>
          </div>

          {/* Badges */}
          <div className="flex flex-wrap gap-2">
            <Badge variant={trust.variant}>
              <TrustIcon className="h-3 w-3 mr-1" />
              {trust.label}
            </Badge>
            <Badge variant={skill.tier === 'python' ? 'warning' : 'success'}>
              {skill.tier === 'python' ? (
                <Code className="h-3 w-3 mr-1" />
              ) : (
                <FileText className="h-3 w-3 mr-1" />
              )}
              {skill.tier === 'python' ? 'Tier 2 Python' : 'Tier 1 Markdown'}
            </Badge>
            {skill.installed && (
              <Badge variant={skill.enabled ? 'success' : 'neutral'}>
                {skill.enabled ? 'Enabled' : 'Disabled'}
              </Badge>
            )}
          </div>

          {/* Capabilities */}
          {skill.capabilities && skill.capabilities.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-[var(--text-primary)] mb-2">Capabilities</h4>
              <div className="flex flex-wrap gap-1.5">
                {skill.capabilities.map((cap) => (
                  <span
                    key={cap}
                    className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-md bg-[var(--surface-secondary)] text-[var(--text-secondary)]"
                  >
                    <Zap className="h-3 w-3" />
                    {cap}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Scan Results */}
          {scanResult && (
            <div className={cn(
              'rounded-lg border p-3',
              scanResult.safe
                ? 'border-success/30 bg-success/5'
                : 'border-danger/30 bg-danger/5',
            )}>
              <div className="flex items-center gap-2 mb-2">
                {scanResult.safe ? (
                  <ShieldCheck className="h-4 w-4 text-success" />
                ) : (
                  <ShieldX className="h-4 w-4 text-danger" />
                )}
                <span className="text-sm font-medium text-[var(--text-primary)]">
                  {scanResult.safe ? 'No issues found' : `${scanResult.issues.length} issue(s) found`}
                </span>
              </div>
              {scanResult.issues.length > 0 && (
                <div className="space-y-1.5">
                  {scanResult.issues.map((issue, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs">
                      <Badge variant={severityVariant[issue.severity] ?? 'neutral'} className="text-[10px] shrink-0">
                        {issue.severity}
                      </Badge>
                      <span className="text-[var(--text-secondary)]">
                        {issue.message}
                        {issue.file && (
                          <span className="text-[var(--text-tertiary)]"> ({issue.file}:{issue.line})</span>
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-wrap gap-2 pt-2 border-t border-[var(--border-default)]">
            {!skill.installed ? (
              <Button
                size="sm"
                onClick={handleInstall}
                loading={installMutation.isPending}
              >
                <Download className="h-3.5 w-3.5" />
                Install
              </Button>
            ) : (
              <>
                <Button
                  size="sm"
                  variant={skill.enabled ? 'secondary' : 'primary'}
                  onClick={handleToggle}
                  loading={toggleMutation.isPending}
                >
                  {skill.enabled ? 'Disable' : 'Enable'}
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={handleUninstall}
                  loading={uninstallMutation.isPending}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Uninstall
                </Button>
              </>
            )}
            <Button
              size="sm"
              variant="ghost"
              onClick={handleScan}
              loading={scanMutation.isPending}
            >
              <Shield className="h-3.5 w-3.5" />
              Security Scan
            </Button>
          </div>
        </div>
      ) : (
        <p className="text-sm text-[var(--text-secondary)]">Skill not found.</p>
      )}
    </Modal>
  )
}
