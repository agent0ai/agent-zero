'use client'

import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import { cn } from '@/lib/cn'
import { X, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react'

type ToastVariant = 'success' | 'warning' | 'danger' | 'info'

interface Toast {
  id: string
  message: string
  variant: ToastVariant
}

interface ToastContextValue {
  toast: (message: string, variant?: ToastVariant) => void
}

const ToastContext = createContext<ToastContextValue>({ toast: () => {} })

export function useToast() {
  return useContext(ToastContext)
}

const icons: Record<ToastVariant, typeof CheckCircle> = {
  success: CheckCircle,
  warning: AlertTriangle,
  danger: AlertCircle,
  info: Info,
}

const variantStyles: Record<ToastVariant, string> = {
  success: 'border-success bg-success-light dark:bg-success/10 text-success-dark dark:text-success',
  warning: 'border-warning bg-warning-light dark:bg-warning/10 text-warning-dark dark:text-warning',
  danger: 'border-danger bg-danger-light dark:bg-danger/10 text-danger-dark dark:text-danger',
  info: 'border-info bg-info-light dark:bg-info/10 text-info-dark dark:text-info',
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const toast = useCallback((message: string, variant: ToastVariant = 'info') => {
    const id = Math.random().toString(36).slice(2)
    setToasts((prev) => [...prev, { id, message, variant }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }, [])

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
        {toasts.map((t) => {
          const Icon = icons[t.variant]
          return (
            <div
              key={t.id}
              className={cn(
                'flex items-center gap-2 rounded-lg border px-4 py-3 shadow-lg',
                'animate-in slide-in-from-right fade-in text-sm',
                variantStyles[t.variant],
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="flex-1">{t.message}</span>
              <button onClick={() => dismiss(t.id)} className="shrink-0 opacity-60 hover:opacity-100">
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}
