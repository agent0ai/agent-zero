'use client'

import Link from 'next/link'

export default function CTASection() {
  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-blue-600 to-purple-600">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-4xl font-bold text-white mb-6">
          Ready to Deploy Smarter?
        </h2>
        <p className="text-xl text-blue-100 mb-8">
          Join thousands of developers using Agent Jumbo for intelligent multi-platform deployments.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/documentation"
            className="px-8 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition"
          >
            Start Free
          </Link>
          <a
            href="https://github.com/agent-zero-deploy/agent-jumbo"
            target="_blank"
            rel="noopener noreferrer"
            className="px-8 py-3 border-2 border-white text-white rounded-lg font-semibold hover:bg-white hover:bg-opacity-10 transition"
          >
            Star on GitHub
          </a>
        </div>
      </div>
    </section>
  )
}
