import { cn } from '@/lib/cn'
import type { HTMLAttributes, TdHTMLAttributes, ThHTMLAttributes } from 'react'

export function Table({ className, ...props }: HTMLAttributes<HTMLTableElement>) {
  return (
    <div className="w-full overflow-auto">
      <table className={cn('w-full caption-bottom text-sm', className)} {...props} />
    </div>
  )
}

export function TableHeader({ className, ...props }: HTMLAttributes<HTMLTableSectionElement>) {
  return <thead className={cn('border-b border-[var(--border-default)]', className)} {...props} />
}

export function TableBody({ className, ...props }: HTMLAttributes<HTMLTableSectionElement>) {
  return <tbody className={cn('[&_tr:last-child]:border-0', className)} {...props} />
}

export function TableRow({ className, ...props }: HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr
      className={cn(
        'border-b border-[var(--border-default)] transition-colors',
        'hover:bg-[var(--surface-secondary)]',
        className,
      )}
      {...props}
    />
  )
}

export function TableHead({ className, ...props }: ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={cn(
        'h-10 px-3 text-left align-middle font-medium text-[var(--text-secondary)] text-xs uppercase tracking-wide',
        className,
      )}
      {...props}
    />
  )
}

export function TableCell({ className, ...props }: TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className={cn('px-3 py-2.5 align-middle text-[var(--text-primary)]', className)} {...props} />
  )
}
