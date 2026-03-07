'use client'

import { useState } from 'react'
import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/Table'
import { Folder, File, ChevronRight, FolderOpen, Trash2 } from 'lucide-react'
import { useFiles, useDeleteFile } from '@/hooks/useFiles'
import { format } from 'date-fns'

function formatSize(bytes?: number): string {
  if (bytes == null) return '--'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

export default function FilesPage() {
  const [currentPath, setCurrentPath] = useState('')
  const { data, isLoading, error } = useFiles(currentPath)
  const deleteMutation = useDeleteFile()

  const files = data?.data?.files ?? []
  const parentPath = data?.data?.parent_path ?? null

  const pathSegments = currentPath
    .split('/')
    .filter(Boolean)
    .reduce<{ name: string; path: string }[]>((acc, seg) => {
      const prev = acc.length > 0 ? acc[acc.length - 1].path : ''
      acc.push({ name: seg, path: prev ? `${prev}/${seg}` : seg })
      return acc
    }, [])

  function handleDelete(path: string, name: string) {
    if (window.confirm(`Delete "${name}"? This cannot be undone.`)) {
      deleteMutation.mutate(path)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Files</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          Browse and manage agent workspace files
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-1 text-sm">
            <button
              onClick={() => setCurrentPath('')}
              className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] font-medium"
            >
              root
            </button>
            {pathSegments.map((seg) => (
              <span key={seg.path} className="flex items-center gap-1">
                <ChevronRight className="h-3 w-3 text-[var(--text-tertiary)]" />
                <button
                  onClick={() => setCurrentPath(seg.path)}
                  className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] font-medium"
                >
                  {seg.name}
                </button>
              </span>
            ))}
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
              Failed to load files. Check that the backend is running.
            </div>
          ) : files.length === 0 ? (
            <EmptyState
              icon={<FolderOpen className="h-10 w-10" />}
              title="Empty directory"
              description="This directory has no files."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Modified</TableHead>
                  <TableHead className="w-12" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {parentPath !== null && (
                  <TableRow
                    className="cursor-pointer"
                    onClick={() => setCurrentPath(parentPath)}
                  >
                    <TableCell className="flex items-center gap-2">
                      <Folder className="h-4 w-4 text-[var(--text-tertiary)]" />
                      <span className="text-[var(--text-secondary)]">..</span>
                    </TableCell>
                    <TableCell>--</TableCell>
                    <TableCell>--</TableCell>
                    <TableCell>--</TableCell>
                    <TableCell />
                  </TableRow>
                )}
                {files.map((file) => (
                  <TableRow
                    key={file.path}
                    className={file.type === 'directory' ? 'cursor-pointer' : ''}
                    onClick={
                      file.type === 'directory'
                        ? () => setCurrentPath(file.path)
                        : undefined
                    }
                  >
                    <TableCell className="flex items-center gap-2">
                      {file.type === 'directory' ? (
                        <Folder className="h-4 w-4 text-brand-500" />
                      ) : (
                        <File className="h-4 w-4 text-[var(--text-tertiary)]" />
                      )}
                      <span className="font-medium">{file.name}</span>
                    </TableCell>
                    <TableCell className="text-[var(--text-secondary)]">
                      {file.type === 'directory' ? 'Folder' : 'File'}
                    </TableCell>
                    <TableCell className="text-[var(--text-secondary)]">
                      {file.type === 'file' ? formatSize(file.size) : '--'}
                    </TableCell>
                    <TableCell className="text-[var(--text-secondary)]">
                      {file.modified
                        ? format(new Date(file.modified), 'MMM d, yyyy HH:mm')
                        : '--'}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(file.path, file.name)
                        }}
                        loading={
                          deleteMutation.isPending &&
                          deleteMutation.variables === file.path
                        }
                      >
                        <Trash2 className="h-4 w-4 text-[var(--text-tertiary)] hover:text-danger" />
                      </Button>
                    </TableCell>
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
