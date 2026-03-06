'use client'

import { cn } from '@/lib/cn'
import { Plus, MessageSquare, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/Button'

export interface ChatContext {
  id: string
  name: string
  log_length: number
}

interface ChatSidebarProps {
  contexts: ChatContext[]
  activeContextId: string | null
  onSelect: (id: string) => void
  onCreate: () => void
  onDelete: (id: string) => void
}

export function ChatSidebar({ contexts, activeContextId, onSelect, onCreate, onDelete }: ChatSidebarProps) {
  return (
    <div className="flex h-full flex-col border-r border-[var(--border-default)] bg-[var(--surface-primary)] w-64">
      <div className="p-3 border-b border-[var(--border-default)]">
        <Button variant="secondary" size="sm" className="w-full" onClick={onCreate}>
          <Plus className="h-4 w-4" /> New Chat
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {contexts.map((ctx) => (
          <button
            key={ctx.id}
            onClick={() => onSelect(ctx.id)}
            className={cn(
              'flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm text-left transition-colors group',
              activeContextId === ctx.id
                ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/20 dark:text-brand-400'
                : 'text-[var(--text-secondary)] hover:bg-[var(--surface-secondary)]',
            )}
          >
            <MessageSquare className="h-3.5 w-3.5 shrink-0" />
            <span className="flex-1 truncate">{ctx.name || `Chat ${ctx.id.slice(0, 6)}`}</span>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onDelete(ctx.id)
              }}
              className="shrink-0 opacity-0 group-hover:opacity-60 hover:!opacity-100 p-0.5 rounded hover:bg-danger-light dark:hover:bg-danger/10"
              aria-label="Delete chat"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          </button>
        ))}
        {contexts.length === 0 && (
          <p className="text-xs text-[var(--text-tertiary)] text-center py-4">
            No conversations yet
          </p>
        )}
      </div>
    </div>
  )
}
