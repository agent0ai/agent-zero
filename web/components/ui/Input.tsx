'use client'

import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react'
import { cn } from '@/lib/cn'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  icon?: ReactNode
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, icon, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')
    return (
      <div className="space-y-1.5">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-[var(--text-primary)]">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              'flex h-9 w-full rounded-md border bg-[var(--surface-primary)] px-3 py-1 text-sm',
              'border-[var(--border-default)] text-[var(--text-primary)]',
              'placeholder:text-[var(--text-tertiary)]',
              'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent',
              'disabled:cursor-not-allowed disabled:opacity-50',
              icon && 'pl-9',
              error && 'border-danger focus:ring-danger',
              className,
            )}
            {...props}
          />
        </div>
        {error && <p className="text-sm text-danger">{error}</p>}
      </div>
    )
  },
)
Input.displayName = 'Input'

export { Input }
