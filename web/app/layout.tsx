import type { Metadata } from 'next'
import './globals.css'
import Header from '@/components/Header'
import Footer from '@/components/Footer'
import AnalyticsClient from '@/components/AnalyticsClient'

export const metadata: Metadata = {
  title: 'Agent Jumbo - Multi-Platform Deployment Orchestration',
  description: 'Intelligent deployment orchestration for AI agents and modern applications',
  icons: {
    icon: '/favicon.svg',
  },
  openGraph: {
    title: 'Agent Jumbo',
    description: 'Multi-platform deployment orchestration with intelligent error handling',
    type: 'website',
    url: 'https://agent-jumbo.com',
    siteName: 'Agent Jumbo',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Agent Jumbo',
    description: 'Intelligent deployment orchestration',
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
      <body className="bg-white dark:bg-slate-950">
        <AnalyticsClient />
        <Header />
        <main className="min-h-screen">{children}</main>
        <Footer />
      </body>
    </html>
  )
}
