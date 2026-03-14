import type { Metadata } from 'next'
import './globals.css'
import AnalyticsClient from '@/components/AnalyticsClient'
import { Providers } from './providers'

export const metadata: Metadata = {
  title: 'Agent Jumbo - Intelligent Application Operating System',
  description: 'Build, test, and deploy AI-powered workflows that integrate with your business systems. Enterprise-grade orchestration, observability, and governance.',
  icons: {
    icon: '/favicon.svg',
  },
  openGraph: {
    title: 'Agent Jumbo',
    description: 'The Operating System for Intelligent Business Applications',
    type: 'website',
    url: 'https://agent-jumbo.com',
    siteName: 'Agent Jumbo',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Agent Jumbo',
    description: 'Operating System for Intelligent Business Applications',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="bg-[var(--surface-primary)] text-[var(--text-primary)]">
        <Providers>
          <AnalyticsClient />
          {children}
        </Providers>
      </body>
    </html>
  )
}
