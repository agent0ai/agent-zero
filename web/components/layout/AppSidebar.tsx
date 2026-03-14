'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/cn'
import { APP_NAVIGATION } from '@/lib/constants'
import { PanelLeftClose, PanelLeft } from 'lucide-react'

interface AppSidebarProps {
  collapsed: boolean
  onToggle: () => void
}

export function AppSidebar({ collapsed, onToggle }: AppSidebarProps) {
  const pathname = usePathname()

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-30 flex h-screen flex-col border-r border-[var(--border-default)]',
        'bg-[var(--surface-primary)] transition-[width] duration-200',
        collapsed ? 'w-[var(--sidebar-collapsed-width)]' : 'w-[var(--sidebar-width)]',
      )}
    >
      {/* Logo */}
      <div className="flex h-[var(--topbar-height)] items-center justify-between border-b border-[var(--border-default)] px-3">
        {!collapsed && (
          <Link href="/overview" className="text-sm font-bold text-[var(--text-primary)] truncate">
            Agent Jumbo
          </Link>
        )}
        <button
          onClick={onToggle}
          className="rounded-md p-1.5 text-[var(--text-tertiary)] hover:bg-[var(--surface-secondary)] hover:text-[var(--text-primary)]"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <PanelLeft className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-4">
        {APP_NAVIGATION.map((group) => (
          <div key={group.label}>
            {!collapsed && (
              <p className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
                {group.label}
              </p>
            )}
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
                const Icon = item.icon
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    title={collapsed ? item.label : undefined}
                    className={cn(
                      'flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors',
                      isActive
                        ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/20 dark:text-brand-400 font-medium'
                        : 'text-[var(--text-secondary)] hover:bg-[var(--surface-secondary)] hover:text-[var(--text-primary)]',
                      collapsed && 'justify-center',
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    {!collapsed && (
                      <span className="truncate">{item.label}</span>
                    )}
                    {!collapsed && item.badge && (
                      <span className="ml-auto rounded-full bg-brand-100 px-1.5 py-0.5 text-[10px] font-medium text-brand-700 dark:bg-brand-900/30 dark:text-brand-400">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Version */}
      {!collapsed && (
        <div className="border-t border-[var(--border-default)] px-4 py-2">
          <p className="text-[10px] text-[var(--text-tertiary)]">v1.0.0-beta</p>
        </div>
      )}
    </aside>
  )
}
