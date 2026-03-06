'use client'

import { usePathname } from 'next/navigation'
import { Search, Bell, User } from 'lucide-react'
import { APP_NAVIGATION } from '@/lib/constants'

interface AppTopBarProps {
  sidebarCollapsed: boolean
}

function getBreadcrumb(pathname: string): string {
  for (const group of APP_NAVIGATION) {
    for (const item of group.items) {
      if (pathname === item.href || pathname.startsWith(item.href + '/')) {
        return item.label
      }
    }
  }
  return 'Overview'
}

export function AppTopBar({ sidebarCollapsed }: AppTopBarProps) {
  const pathname = usePathname()
  const breadcrumb = getBreadcrumb(pathname)

  return (
    <header
      className="sticky top-0 z-20 flex h-[var(--topbar-height)] items-center justify-between border-b border-[var(--border-default)] bg-[var(--surface-primary)] px-4"
      style={{
        marginLeft: sidebarCollapsed
          ? 'var(--sidebar-collapsed-width)'
          : 'var(--sidebar-width)',
        transition: 'margin-left 200ms',
      }}
    >
      <div className="flex items-center gap-2 text-sm">
        <span className="text-[var(--text-tertiary)]">App</span>
        <span className="text-[var(--text-tertiary)]">/</span>
        <span className="font-medium text-[var(--text-primary)]">{breadcrumb}</span>
      </div>

      <div className="flex items-center gap-1">
        <button
          className="rounded-md p-2 text-[var(--text-tertiary)] hover:bg-[var(--surface-secondary)] hover:text-[var(--text-primary)]"
          aria-label="Search"
        >
          <Search className="h-4 w-4" />
        </button>
        <button
          className="rounded-md p-2 text-[var(--text-tertiary)] hover:bg-[var(--surface-secondary)] hover:text-[var(--text-primary)]"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
        </button>
        <button
          className="rounded-md p-2 text-[var(--text-tertiary)] hover:bg-[var(--surface-secondary)] hover:text-[var(--text-primary)]"
          aria-label="User menu"
        >
          <User className="h-4 w-4" />
        </button>
      </div>
    </header>
  )
}
