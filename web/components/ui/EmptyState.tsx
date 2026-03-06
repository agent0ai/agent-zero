import { cn } from '@/lib/cn'
import type { ReactNode } from 'react'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)}>
      {icon && <div className="mb-4 text-[var(--text-tertiary)]">{icon}</div>}
      <h3 className="text-lg font-semibold text-[var(--text-primary)]">{title}</h3>
      {description && (
        <p className="mt-1 max-w-sm text-sm text-[var(--text-secondary)]">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
