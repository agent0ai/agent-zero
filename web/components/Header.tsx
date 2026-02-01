'use client'

import Link from 'next/link'
import { useState } from 'react'

export default function Header() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <header className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="font-bold text-xl text-slate-900 dark:text-white">
          🚀 Agent Jumbo
        </Link>
        <ul className="hidden md:flex gap-8">
          <li>
            <Link href="/" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white">
              Home
            </Link>
          </li>
          <li>
            <Link href="/documentation" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white">
              Docs
            </Link>
          </li>
          <li>
            <Link href="/dashboard" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white">
              Dashboard
            </Link>
          </li>
          <li>
            <a href="https://github.com/agent-zero-deploy/agent-jumbo" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white">
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
    </header>
  )
}
