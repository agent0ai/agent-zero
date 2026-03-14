'use client'

import Link from 'next/link'

export default function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white mb-4">Product</h3>
            <ul className="space-y-2">
              <li><Link href="/documentation" className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">Documentation</Link></li>
              <li><Link href="/overview" className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">Dashboard</Link></li>
              <li><a href="https://github.com/agent-jumbo-deploy/agent-jumbo" target="_blank" rel="noopener noreferrer" className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">GitHub</a></li>
            </ul>
          </div>
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white mb-4">Resources</h3>
            <ul className="space-y-2">
              <li><a href="#" className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">Blog</a></li>
              <li><a href="#" className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">Examples</a></li>
              <li><a href="#" className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">API Reference</a></li>
            </ul>
          </div>
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white mb-4">Legal</h3>
            <ul className="space-y-2">
              <li><a href="#" className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">Privacy</a></li>
              <li><a href="#" className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">Security</a></li>
              <li><a href="#" className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">License</a></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-slate-200 dark:border-slate-800 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-slate-600 dark:text-slate-400">© {currentYear} Mahoosuc Solutions. All rights reserved.</p>
          <p className="text-slate-600 dark:text-slate-400">Apache License 2.0</p>
        </div>
      </div>
    </footer>
  )
}
