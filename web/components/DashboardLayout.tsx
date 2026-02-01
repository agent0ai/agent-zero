'use client'

import { ReactNode } from 'react'

interface DashboardLayoutProps {
  children: ReactNode
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="flex">
      <aside className="w-64 border-r border-slate-200 dark:border-slate-800 p-6 hidden md:block">
        <nav className="space-y-4">
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white mb-2">Navigation</h3>
            <ul className="space-y-1">
              <li><a href="#" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white">Overview</a></li>
              <li><a href="#" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white">Deployments</a></li>
              <li><a href="#" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white">Configuration</a></li>
              <li><a href="#" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white">Logs</a></li>
            </ul>
          </div>
        </nav>
      </aside>

      <main className="flex-1 p-6 sm:p-8">
        {children}
      </main>
    </div>
  )
}
