'use client'

import { cn } from '@/lib/cn'
import { Loader2 } from 'lucide-react'

interface ChatProgressProps {
  message?: string
  active?: boolean
}

export function ChatProgress({ message, active }: ChatProgressProps) {
  if (!message && !active) return null

  return (
    <div className="flex items-center gap-2 px-4 py-2 text-xs text-[var(--text-secondary)]">
      <Loader2 className={cn('h-3 w-3', active && 'animate-spin')} />
      <span>{message || 'Processing...'}</span>
    </div>
  )
}
