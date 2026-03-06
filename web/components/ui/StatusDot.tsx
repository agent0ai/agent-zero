import { cn } from '@/lib/cn'

const colors = {
  success: 'bg-success',
  warning: 'bg-warning',
  danger: 'bg-danger',
  info: 'bg-info',
  neutral: 'bg-slate-400',
} as const

interface StatusDotProps {
  status: keyof typeof colors
  pulse?: boolean
  className?: string
}

export function StatusDot({ status, pulse, className }: StatusDotProps) {
  return (
    <span className={cn('relative inline-flex h-2.5 w-2.5 rounded-full', colors[status], className)}>
      {pulse && (
        <span
          className={cn(
            'absolute inline-flex h-full w-full animate-ping rounded-full opacity-75',
            colors[status],
          )}
        />
      )}
    </span>
  )
}
