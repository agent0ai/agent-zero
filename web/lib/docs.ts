import fs from 'fs'
import path from 'path'
import matter from 'gray-matter'
import { marked } from 'marked'

const DOCS_DIR = path.join(process.cwd(), '..', 'docs')

export interface DocMetadata {
  title: string
  description: string
  author?: string
  date?: string
  [key: string]: any
}

export interface DocFile {
  slug: string
  metadata: DocMetadata
  content: string
  html: string
}

export function getAllDocs(): DocFile[] {
  const files = fs.readdirSync(DOCS_DIR)
    .filter(file => file.endsWith('.md'))
    .filter(file => !file.startsWith('_'))

  return files.map(file => getDoc(file.replace('.md', '')))
}

export function getDoc(slug: string): DocFile {
  const filePath = path.join(DOCS_DIR, `${slug}.md`)
  const fileContent = fs.readFileSync(filePath, 'utf-8')
  const { data, content } = matter(fileContent)
  const html = marked(content)

  return {
    slug,
    metadata: data as DocMetadata,
    content,
    html,
  }
}

export function getDocSlugs(): string[] {
  return getAllDocs().map(doc => doc.slug)
}

export function getRelatedDocs(slug: string, limit: number = 3): DocFile[] {
  const allDocs = getAllDocs()
  const currentDoc = allDocs.find(doc => doc.slug === slug)

  if (!currentDoc) return []

  return allDocs
    .filter(doc => doc.slug !== slug)
    .sort((a, b) => {
      const aDate = new Date(a.metadata.date || 0).getTime()
      const bDate = new Date(b.metadata.date || 0).getTime()
      return bDate - aDate
    })
    .slice(0, limit)
}

export const FEATURED_DOCS = [
  'README',
  'INSTALL',
  'CONTRIBUTING',
]
