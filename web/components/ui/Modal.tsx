'use client'

import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { ReactNode } from 'react'

interface ModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  children: ReactNode
  className?: string
}

export function Modal({ open, onOpenChange, title, description, children, className }: ModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm animate-in fade-in" />
        <Dialog.Content
          className={cn(
            'fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2',
            'w-full max-w-lg rounded-lg border border-[var(--border-default)]',
            'bg-[var(--surface-primary)] p-6 shadow-lg',
            'animate-in fade-in zoom-in-95',
            className,
          )}
        >
          <div className="flex items-start justify-between mb-4">
            <div>
              <Dialog.Title className="text-lg font-semibold text-[var(--text-primary)]">
                {title}
              </Dialog.Title>
              {description && (
                <Dialog.Description className="mt-1 text-sm text-[var(--text-secondary)]">
                  {description}
                </Dialog.Description>
              )}
            </div>
            <Dialog.Close className="rounded-md p-1 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-tertiary)]">
              <X className="h-4 w-4" />
            </Dialog.Close>
          </div>
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
