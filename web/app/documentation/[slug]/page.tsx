import { getDoc, getDocSlugs, getRelatedDocs } from '@/lib/docs'
import Link from 'next/link'

export async function generateStaticParams() {
  const slugs = getDocSlugs()
  return slugs.map(slug => ({ slug }))
}

export default function DocPage({ params }: { params: { slug: string } }) {
  const doc = getDoc(params.slug)
  const relatedDocs = getRelatedDocs(params.slug, 3)

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-8">
        <Link
          href="/documentation"
          className="text-blue-600 dark:text-blue-400 hover:underline mb-4 inline-block"
        >
          ← Back to Docs
        </Link>
        <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
          {doc.metadata.title || doc.slug}
        </h1>
        {doc.metadata.description && (
          <p className="text-xl text-slate-600 dark:text-slate-300">
            {doc.metadata.description}
          </p>
        )}
        {doc.metadata.date && (
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-4">
            Updated {new Date(doc.metadata.date).toLocaleDateString()}
          </p>
        )}
      </div>

      <div className="prose dark:prose-invert max-w-none mb-12" dangerouslySetInnerHTML={{ __html: sanitizeHtml(doc.html) }} />

      {relatedDocs.length > 0 && (
        <div className="mt-12 pt-8 border-t border-slate-200 dark:border-slate-700">
          <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
            Related Documentation
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {relatedDocs.map(relDoc => (
              <Link
                key={relDoc.slug}
                href={`/documentation/${relDoc.slug}`}
                className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:border-blue-500 hover:shadow-lg transition"
              >
                <h4 className="font-bold text-slate-900 dark:text-white mb-2">
                  {relDoc.metadata.title || relDoc.slug}
                </h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2">
                  {relDoc.metadata.description}
                </p>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Basic HTML sanitization to prevent XSS
function sanitizeHtml(html: string): string {
  return html
    .replace(/on\w+\s*=/g, '')
    .replace(/<script[^>]*>.*?<\/script>/gi, '')
    .replace(/<iframe[^>]*>.*?<\/iframe>/gi, '')
}
