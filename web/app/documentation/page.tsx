import Link from 'next/link'
import { getAllDocs } from '@/lib/docs'

export default function DocsIndex() {
  const docs = getAllDocs()
    .filter(doc => doc.metadata.title)
    .sort((a, b) => {
      const aDate = new Date(a.metadata.date || 0).getTime()
      const bDate = new Date(b.metadata.date || 0).getTime()
      return bDate - aDate
    })

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-12">
        <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
          Documentation
        </h1>
        <p className="text-xl text-slate-600 dark:text-slate-300">
          Learn how to use Agent Jumbo for intelligent multi-platform deployment orchestration.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {docs.map(doc => (
          <Link
            key={doc.slug}
            href={`/documentation/${doc.slug}`}
            className="p-6 border border-slate-200 dark:border-slate-700 rounded-lg hover:border-blue-500 dark:hover:border-blue-400 hover:shadow-lg transition"
          >
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
              {doc.metadata.title || doc.slug}
            </h3>
            <p className="text-slate-600 dark:text-slate-400 line-clamp-3">
              {doc.metadata.description || 'Documentation page'}
            </p>
          </Link>
        ))}
      </div>
    </div>
  )
}
