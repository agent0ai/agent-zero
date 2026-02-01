'use client'

import Link from 'next/link'

export default function HeroSection() {
  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div>
          <h1 className="text-5xl sm:text-6xl font-bold text-slate-900 dark:text-white mb-6 leading-tight">
            The Operating System for Intelligent Business Applications
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-300 mb-8 leading-relaxed">
            Build, test, and deploy AI-powered workflows that integrate with your existing systems.
            Agent Zero handles orchestration, observability, cost management, and governance so your
            teams can focus on business logic.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Link
              href="/demo"
              className="px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition text-center"
            >
              Get Demo
            </Link>
            <Link
              href="/documentation"
              className="px-8 py-3 border-2 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg font-semibold hover:bg-slate-50 dark:hover:bg-slate-900 transition text-center"
            >
              View Documentation
            </Link>
          </div>
        </div>
        <div className="bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 rounded-xl p-8 h-96 flex items-center justify-center">
          <div className="text-center">
            <div className="text-6xl mb-4">🚀</div>
            <p className="text-slate-600 dark:text-slate-300 font-semibold">
              Deployment Architecture Dashboard
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
