'use client'

import { useState } from 'react'
import { cn } from '@/lib/cn'
import { ChevronDown, Cpu } from 'lucide-react'
import { api } from '@/lib/api/client'

interface ModelSelectorProps {
  className?: string
}

export function ModelSelector({ className }: ModelSelectorProps) {
  const [open, setOpen] = useState(false)
  const [current, setCurrent] = useState('Default Model')

  const switchModel = async (model: string) => {
    try {
      await api('model_selector_quick_switch', { body: { model } })
      setCurrent(model)
    } catch {
      // Model switch failed silently
    }
    setOpen(false)
  }

  return (
    <div className={cn('relative', className)}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 rounded-md border border-[var(--border-default)] px-2.5 py-1.5 text-xs text-[var(--text-secondary)] hover:bg-[var(--surface-secondary)]"
      >
        <Cpu className="h-3.5 w-3.5" />
        <span className="truncate max-w-[120px]">{current}</span>
        <ChevronDown className="h-3 w-3" />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute top-full mt-1 left-0 z-50 w-52 rounded-md border border-[var(--border-default)] bg-[var(--surface-primary)] p-1 shadow-lg">
            {['gpt-4o', 'claude-sonnet-4-20250514', 'claude-opus-4-20250514', 'gemini-2.0-flash'].map((m) => (
              <button
                key={m}
                onClick={() => switchModel(m)}
                className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-xs text-[var(--text-primary)] hover:bg-[var(--surface-secondary)]"
              >
                <Cpu className="h-3 w-3 text-[var(--text-tertiary)]" />
                {m}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
