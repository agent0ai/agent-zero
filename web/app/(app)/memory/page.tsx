'use client'

import { useState, useMemo } from 'react'
import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/Table'
import { Brain, Search } from 'lucide-react'
import { useMemoryDashboard } from '@/hooks/useMemory'

export default function MemoryPage() {
  const { data, isLoading, error } = useMemoryDashboard()
  const [search, setSearch] = useState('')

  const memories = data?.memories ?? []

  const filtered = useMemo(() => {
    if (!search.trim()) return memories
    const q = search.toLowerCase()
    return memories.filter((m) =>
      Object.values(m).some(
        (v) => typeof v === 'string' && v.toLowerCase().includes(q),
      ),
    )
  }, [memories, search])

  const fieldKeys = useMemo(() => {
    if (memories.length === 0) return []
    const keys = new Set<string>()
    memories.forEach((m) => Object.keys(m).forEach((k) => keys.add(k)))
    return Array.from(keys)
  }, [memories])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Memory</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          Agent memory and knowledge management
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardBody className="flex items-center gap-3">
            <div className="rounded-lg bg-brand-100 dark:bg-brand-900/30 p-2.5">
              <Brain className="h-5 w-5 text-brand-600 dark:text-brand-400" />
            </div>
            <div>
              <p className="text-sm text-[var(--text-secondary)]">Total Memories</p>
              <p className="text-2xl font-bold text-[var(--text-primary)]">
                {isLoading ? '--' : memories.length}
              </p>
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardBody className="flex items-center gap-3">
            <div className="rounded-lg bg-info-light dark:bg-info/20 p-2.5">
              <Search className="h-5 w-5 text-info-dark dark:text-info" />
            </div>
            <div>
              <p className="text-sm text-[var(--text-secondary)]">Filtered</p>
              <p className="text-2xl font-bold text-[var(--text-primary)]">
                {isLoading ? '--' : filtered.length}
              </p>
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardBody className="flex items-center gap-3">
            <div className="rounded-lg bg-success-light dark:bg-success/20 p-2.5">
              <Brain className="h-5 w-5 text-success-dark dark:text-success" />
            </div>
            <div>
              <p className="text-sm text-[var(--text-secondary)]">Fields</p>
              <p className="text-2xl font-bold text-[var(--text-primary)]">
                {isLoading ? '--' : fieldKeys.length}
              </p>
            </div>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <h2 className="font-semibold text-[var(--text-primary)]">Memory Store</h2>
            <div className="w-64">
              <Input
                placeholder="Search memories..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                icon={<Search className="h-4 w-4" />}
              />
            </div>
          </div>
        </CardHeader>
        <CardBody className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : error ? (
            <div className="p-4 text-sm text-danger">
              Failed to load memories. Check that the backend is running.
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={<Brain className="h-10 w-10" />}
              title={search ? 'No matches' : 'No memories'}
              description={
                search
                  ? 'Try adjusting your search query.'
                  : 'The agent has not stored any memories yet.'
              }
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  {fieldKeys.map((key) => (
                    <TableHead key={key}>{key}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((memory, idx) => (
                  <TableRow key={idx}>
                    {fieldKeys.map((key) => (
                      <TableCell key={key} className="max-w-xs truncate">
                        {memory[key] != null ? (
                          typeof memory[key] === 'object' ? (
                            <Badge variant="neutral">
                              {JSON.stringify(memory[key]).slice(0, 60)}
                            </Badge>
                          ) : (
                            String(memory[key])
                          )
                        ) : (
                          <span className="text-[var(--text-tertiary)]">--</span>
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardBody>
      </Card>
    </div>
  )
}
