'use client'

import { cn } from '@/lib/cn'
import { User, Bot, AlertTriangle, AlertCircle, Info, Terminal, Globe } from 'lucide-react'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import type { ReactNode } from 'react'

export interface ChatLog {
  id: string | number
  no: number
  type: string
  heading?: string
  content: string
  temp?: boolean
  kvps?: Record<string, unknown>
}

const typeConfig: Record<string, { icon: ReactNode; align: string; style: string }> = {
  user: {
    icon: <User className="h-4 w-4" />,
    align: 'justify-end',
    style: 'bg-brand-600 text-white',
  },
  response: {
    icon: <Bot className="h-4 w-4" />,
    align: 'justify-start',
    style: 'bg-[var(--surface-secondary)] text-[var(--text-primary)] border border-[var(--border-default)]',
  },
  agent: {
    icon: <Bot className="h-4 w-4" />,
    align: 'justify-start',
    style: 'bg-[var(--surface-tertiary)] text-[var(--text-primary)] border border-[var(--border-default)]',
  },
  tool: {
    icon: <Terminal className="h-4 w-4" />,
    align: 'justify-start',
    style: 'bg-slate-800 text-slate-100 dark:bg-slate-900',
  },
  code_exe: {
    icon: <Terminal className="h-4 w-4" />,
    align: 'justify-start',
    style: 'bg-slate-800 text-slate-100 dark:bg-slate-900',
  },
  browser: {
    icon: <Globe className="h-4 w-4" />,
    align: 'justify-start',
    style: 'bg-[var(--surface-tertiary)] text-[var(--text-primary)] border border-[var(--border-default)]',
  },
  warning: {
    icon: <AlertTriangle className="h-4 w-4" />,
    align: 'justify-center',
    style: 'bg-warning-light text-warning-dark dark:bg-warning/10 dark:text-warning',
  },
  error: {
    icon: <AlertCircle className="h-4 w-4" />,
    align: 'justify-center',
    style: 'bg-danger-light text-danger-dark dark:bg-danger/10 dark:text-danger',
  },
  info: {
    icon: <Info className="h-4 w-4" />,
    align: 'justify-center',
    style: 'bg-info-light text-info-dark dark:bg-info/10 dark:text-info',
  },
}

function getConfig(type: string) {
  return typeConfig[type] || typeConfig.agent
}

function sanitizeMarkdown(content: string): string {
  const raw = marked.parse(content, { breaks: true }) as string
  if (typeof window === 'undefined') return raw
  return DOMPurify.sanitize(raw, {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li', 'code', 'pre', 'a', 'blockquote', 'table', 'thead',
      'tbody', 'tr', 'th', 'td', 'img', 'span', 'div', 'hr',
    ],
    ALLOWED_ATTR: ['href', 'title', 'target', 'rel', 'src', 'alt', 'class'],
  })
}

function KvpTable({ kvps }: { kvps: Record<string, unknown> }) {
  return (
    <div className="mt-2 text-xs">
      {Object.entries(kvps).map(([key, value]) => {
        if (key === 'tool_args' && typeof value === 'object' && value) {
          return Object.entries(value as Record<string, unknown>).map(([k, v]) => (
            <KvpRow key={k} label={k} value={v} />
          ))
        }
        return <KvpRow key={key} label={key} value={value} />
      })}
    </div>
  )
}

function KvpRow({ label, value }: { label: string; value: unknown }) {
  const displayLabel = label.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
  const displayValue = typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value ?? '')
  const isThought = label === 'thoughts' || label === 'reasoning'

  return (
    <div className={cn('flex gap-2 py-1 border-t border-white/10', isThought && 'opacity-70 italic')}>
      <span className="shrink-0 font-medium opacity-70 w-24">{displayLabel}</span>
      <pre className="flex-1 whitespace-pre-wrap break-words font-mono text-[11px] overflow-auto max-h-40">
        {displayValue}
      </pre>
    </div>
  )
}

export function ChatMessage({ log }: { log: ChatLog }) {
  const config = getConfig(log.type)
  const isUser = log.type === 'user'
  const isMarkdown = log.type === 'response'

  return (
    <div className={cn('flex w-full', config.align)}>
      <div
        className={cn(
          'rounded-lg px-3 py-2 text-sm max-w-[85%] lg:max-w-[70%]',
          config.style,
          log.temp && 'opacity-60',
        )}
      >
        {log.heading && (
          <div className="flex items-center gap-1.5 mb-1">
            {config.icon}
            <span className="font-semibold text-xs opacity-80">{log.heading}</span>
          </div>
        )}

        {log.content && log.content.trim() && (
          isMarkdown ? (
            <div
              className="prose prose-sm dark:prose-invert max-w-none [&_pre]:bg-slate-900 [&_pre]:text-slate-100 [&_code]:text-xs"
              dangerouslySetInnerHTML={{ __html: sanitizeMarkdown(log.content) }}
            />
          ) : (
            <pre className={cn(
              'whitespace-pre-wrap break-words font-mono text-xs',
              isUser && 'font-sans text-sm',
            )}>
              {log.content}
            </pre>
          )
        )}

        {log.kvps && Object.keys(log.kvps).length > 0 && (
          <KvpTable kvps={log.kvps} />
        )}
      </div>
    </div>
  )
}
