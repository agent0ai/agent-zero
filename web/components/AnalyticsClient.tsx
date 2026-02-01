'use client'

import { useEffect } from 'react'
import { initializeAnalytics } from '@/lib/analytics'

export default function AnalyticsClient() {
  useEffect(() => {
    const gaId = process.env.NEXT_PUBLIC_GA_ID
    if (gaId) {
      initializeAnalytics(gaId)
    }
  }, [])

  return null
}
