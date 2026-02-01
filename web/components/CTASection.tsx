'use client'

import Link from 'next/link'

export default function CTASection() {
  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-blue-600 to-purple-600">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-4xl font-bold text-white mb-6">
          Ready to Build Intelligent Applications?
        </h2>
        <p className="text-xl text-blue-100 mb-8">
          See how enterprises are building AI-powered workflows that integrate with their business systems.
          Get a custom demo tailored to your use case.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/demo"
            className="px-8 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition"
          >
            Get Demo
          </Link>
          <Link
            href="/documentation"
            className="px-8 py-3 border-2 border-white text-white rounded-lg font-semibold hover:bg-white hover:bg-opacity-10 transition"
          >
            View Use Cases
          </Link>
        </div>
      </div>
    </section>
  )
}
