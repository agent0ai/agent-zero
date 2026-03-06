'use client'

import { useEffect, useState, useCallback, type ReactNode } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { Search } from 'lucide-react'
import { cn } from '@/lib/cn'

export interface CommandItem {
  id: string
  label: string
  icon?: ReactNode
  shortcut?: string
  onSelect: () => void
  group?: string
}

interface CommandPaletteProps {
  items: CommandItem[]
}

export function CommandPalette({ items }: CommandPaletteProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((o) => !o)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  const filtered = items.filter((item) =>
    item.label.toLowerCase().includes(query.toLowerCase()),
  )

  const groups = Array.from(new Set(filtered.map((i) => i.group || 'Actions')))

  const handleSelect = useCallback(
    (item: CommandItem) => {
      item.onSelect()
      setOpen(false)
      setQuery('')
    },
    [],
  )

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-[20%] z-50 w-full max-w-lg -translate-x-1/2 rounded-lg border border-[var(--border-default)] bg-[var(--surface-primary)] shadow-2xl">
          <Dialog.Title className="sr-only">Command palette</Dialog.Title>
          <div className="flex items-center gap-2 border-b border-[var(--border-default)] px-3">
            <Search className="h-4 w-4 text-[var(--text-tertiary)]" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Type a command or search..."
              className="flex-1 bg-transparent py-3 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] outline-none"
              autoFocus
            />
            <kbd className="hidden sm:inline-flex h-5 items-center rounded border border-[var(--border-default)] px-1.5 text-[10px] text-[var(--text-tertiary)]">
              ESC
            </kbd>
          </div>
          <div className="max-h-72 overflow-y-auto p-2">
            {groups.map((group) => (
              <div key={group}>
                <div className="px-2 py-1.5 text-xs font-medium text-[var(--text-tertiary)]">
                  {group}
                </div>
                {filtered
                  .filter((i) => (i.group || 'Actions') === group)
                  .map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleSelect(item)}
                      className={cn(
                        'flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm',
                        'text-[var(--text-primary)] hover:bg-[var(--surface-secondary)]',
                      )}
                    >
                      {item.icon && <span className="text-[var(--text-tertiary)]">{item.icon}</span>}
                      <span className="flex-1 text-left">{item.label}</span>
                      {item.shortcut && (
                        <kbd className="text-[10px] text-[var(--text-tertiary)]">{item.shortcut}</kbd>
                      )}
                    </button>
                  ))}
              </div>
            ))}
            {filtered.length === 0 && (
              <div className="py-6 text-center text-sm text-[var(--text-tertiary)]">
                No results found.
              </div>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
