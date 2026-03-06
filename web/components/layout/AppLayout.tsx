'use client'

import { useState, useEffect, type ReactNode } from 'react'
import { AppSidebar } from './AppSidebar'
import { AppTopBar } from './AppTopBar'
import { MobileBottomNav } from './MobileBottomNav'

const SIDEBAR_KEY = 'a0-sidebar-collapsed'

export function AppLayout({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem(SIDEBAR_KEY)
    if (saved === 'true') setCollapsed(true)
  }, [])

  const toggle = () => {
    setCollapsed((prev) => {
      localStorage.setItem(SIDEBAR_KEY, String(!prev))
      return !prev
    })
  }

  return (
    <div className="min-h-screen bg-[var(--surface-secondary)]">
      {/* Desktop sidebar */}
      <div className="hidden md:block">
        <AppSidebar collapsed={collapsed} onToggle={toggle} />
      </div>

      {/* Top bar */}
      <div className="hidden md:block">
        <AppTopBar sidebarCollapsed={collapsed} />
      </div>

      {/* Main content */}
      <main
        className="p-4 pb-20 md:pb-4 md:pt-4 transition-[margin-left] duration-200"
        style={{
          marginLeft: collapsed
            ? 'var(--sidebar-collapsed-width)'
            : 'var(--sidebar-width)',
        }}
      >
        <div className="hidden md:block" style={{ height: 'var(--topbar-height)' }} />
        {children}
      </main>

      {/* Mobile bottom nav */}
      <MobileBottomNav />
    </div>
  )
}
