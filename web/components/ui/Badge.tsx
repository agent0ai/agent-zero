import { cn } from '@/lib/cn'
import type { HTMLAttributes } from 'react'

const variants = {
  success: 'bg-success-light text-success-dark dark:bg-success/20 dark:text-success',
  warning: 'bg-warning-light text-warning-dark dark:bg-warning/20 dark:text-warning',
  danger: 'bg-danger-light text-danger-dark dark:bg-danger/20 dark:text-danger',
  info: 'bg-info-light text-info-dark dark:bg-info/20 dark:text-info',
  neutral: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
} as const

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: keyof typeof variants
}

export function Badge({ variant = 'neutral', className, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        variants[variant],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  )
}
