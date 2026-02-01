import type { Metadata } from 'next'
import './globals.css'
import Header from '@/components/Header'
import Footer from '@/components/Footer'

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
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-white dark:bg-slate-950">
        <Header />
        <main className="min-h-screen">{children}</main>
        <Footer />
      </body>
    </html>
  )
}
