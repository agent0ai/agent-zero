'use client'

import Link from 'next/link'
import { useState } from 'react'

export default function Header() {
  const [isOpen, setIsOpen] = useState(false)

  const trackNavClick = (label: string) => {
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', 'navigation_click', {
        location: label,
      })
    }
  }

  const trackExternalClick = (url: string) => {
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', 'external_link_click', {
        url: url,
      })
    }
  }

  return (
    <header className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="font-bold text-xl text-slate-900 dark:text-white" onClick={() => trackNavClick('Home')}>
          🚀 Agent Jumbo
        </Link>
        <ul className="hidden md:flex gap-8">
          <li>
            <Link href="/" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white" onClick={() => trackNavClick('Home')}>
              Home
            </Link>
          </li>
          <li>
            <Link href="/documentation" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white" onClick={() => trackNavClick('Docs')}>
              Docs
            </Link>
          </li>
          <li>
            <Link href="/overview" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white" onClick={() => trackNavClick('Dashboard')}>
              Dashboard
            </Link>
          </li>
          <li>
            <a href="https://github.com/agent-jumbo-deploy/agent-jumbo" target="_blank" rel="noopener noreferrer" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white" onClick={() => trackExternalClick('GitHub')}>
              GitHub
            </a>
          </li>
        </ul>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="md:hidden p-2"
          aria-label="Toggle menu"
        >
          ☰
        </button>
      </nav>
      {isOpen && (
        <nav className="md:hidden border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 space-y-2">
            <Link href="/" className="block px-3 py-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded" onClick={() => { trackNavClick('Home'); setIsOpen(false) }}>
              Home
            </Link>
            <Link href="/documentation" className="block px-3 py-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded" onClick={() => { trackNavClick('Docs'); setIsOpen(false) }}>
              Docs
            </Link>
            <Link href="/overview" className="block px-3 py-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded" onClick={() => { trackNavClick('Dashboard'); setIsOpen(false) }}>
              Dashboard
            </Link>
            <a href="https://github.com/agent-jumbo-deploy/agent-jumbo" target="_blank" rel="noopener noreferrer" className="block px-3 py-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded" onClick={() => { trackExternalClick('GitHub'); setIsOpen(false) }}>
              GitHub
            </a>
          </div>
        </nav>
      )}
    </header>
  )
}
