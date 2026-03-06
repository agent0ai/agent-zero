'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/cn'
import { MessageSquare, LayoutDashboard, Rocket, Eye, MoreHorizontal } from 'lucide-react'

const items = [
  { label: 'Chat', href: '/chat', icon: MessageSquare },
  { label: 'Overview', href: '/overview', icon: LayoutDashboard },
  { label: 'Deploy', href: '/deployments', icon: Rocket },
  { label: 'Observe', href: '/observability', icon: Eye },
  { label: 'More', href: '/settings', icon: MoreHorizontal },
]

export function MobileBottomNav() {
  const pathname = usePathname()

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 flex items-center justify-around border-t border-[var(--border-default)] bg-[var(--surface-primary)] py-1 md:hidden">
      {items.map((item) => {
        const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
        const Icon = item.icon
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'flex flex-col items-center gap-0.5 px-3 py-1.5 text-[10px]',
              isActive
                ? 'text-brand-600 dark:text-brand-400'
                : 'text-[var(--text-tertiary)]',
            )}
          >
            <Icon className="h-5 w-5" />
            <span>{item.label}</span>
          </Link>
        )
      })}
    </nav>
  )
}
