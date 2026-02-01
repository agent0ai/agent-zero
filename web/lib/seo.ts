import { Metadata } from 'next'

export interface SEOMetadata {
  title: string
  description: string
  image?: string
  url?: string
  author?: string
  type?: string
}

export function generateMetadata(seo: SEOMetadata): Metadata {
  const baseUrl = process.env.NEXT_PUBLIC_URL || 'https://agent-jumbo.vercel.app'
  const imageUrl = seo.image || `${baseUrl}/og-image.png`
  const url = seo.url || baseUrl

  return {
    title: seo.title,
    description: seo.description,
    authors: seo.author ? [{ name: seo.author }] : [],
    openGraph: {
      title: seo.title,
      description: seo.description,
      url: url,
      images: [
        {
          url: imageUrl,
          width: 1200,
          height: 630,
          alt: seo.title,
        },
      ],
      type: (seo.type as any) || 'website',
      siteName: 'Agent Jumbo',
    },
    twitter: {
      card: 'summary_large_image',
      title: seo.title,
      description: seo.description,
      images: [imageUrl],
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
}

export function generateStructuredData(type: string, data: Record<string, any>) {
  return {
    '@context': 'https://schema.org',
    '@type': type,
    ...data,
  }
}
