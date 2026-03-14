'use client'

import { useState } from 'react'
import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { Spinner } from '@/components/ui/Spinner'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/Table'
import { Archive, Download, RotateCcw, Plus } from 'lucide-react'
import { useBackupPreview, useCreateBackup } from '@/hooks/useBackups'

function formatSize(bytes?: number): string {
  if (bytes == null) return '--'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

export default function BackupsPage() {
  const [modalOpen, setModalOpen] = useState(false)
  const [backupName, setBackupName] = useState('agent-jumbo-backup')
  const { data: previewData, isLoading: previewLoading } = useBackupPreview()
  const createBackup = useCreateBackup()

  const groups = previewData?.data?.groups ?? []

  function handleCreate() {
    createBackup.mutate(backupName, {
      onSuccess: () => {
        setModalOpen(false)
        setBackupName('agent-jumbo-backup')
      },
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Backups</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Create and restore system backups
          </p>
        </div>
        <Button size="sm" onClick={() => setModalOpen(true)}>
          <Plus className="h-4 w-4" /> Create Backup
        </Button>
      </div>

      <Modal
        open={modalOpen}
        onOpenChange={setModalOpen}
        title="Create Backup"
        description="Create a new backup of your agent configuration and data."
      >
        <div className="space-y-4">
          <Input
            label="Backup Name"
            value={backupName}
            onChange={(e) => setBackupName(e.target.value)}
            placeholder="agent-jumbo-backup"
          />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              loading={createBackup.isPending}
              disabled={!backupName.trim()}
            >
              {createBackup.isPending ? (
                <>
                  <Spinner size="sm" /> Creating...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4" /> Create
                </>
              )}
            </Button>
          </div>
          {createBackup.isError && (
            <p className="text-sm text-danger">
              Failed to create backup. Please try again.
            </p>
          )}
        </div>
      </Modal>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Archive className="h-4 w-4 text-[var(--text-secondary)]" />
            <h2 className="font-semibold text-[var(--text-primary)]">Backup Preview</h2>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            Items that will be included in the next backup
          </p>
        </CardHeader>
        <CardBody className="p-0">
          {previewLoading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : groups.length === 0 ? (
            <EmptyState
              icon={<Archive className="h-10 w-10" />}
              title="No preview data"
              description="Could not load backup preview. Ensure the backend is running."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Category</TableHead>
                  <TableHead>Items</TableHead>
                  <TableHead>Size</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {groups.map((group) => (
                  <TableRow key={group.category}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <RotateCcw className="h-4 w-4 text-[var(--text-tertiary)]" />
                        <span className="font-medium">{group.category}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {group.items.slice(0, 5).map((item) => (
                          <Badge key={item} variant="neutral">
                            {item}
                          </Badge>
                        ))}
                        {group.items.length > 5 && (
                          <Badge variant="info">
                            +{group.items.length - 5} more
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-[var(--text-secondary)]">
                      {formatSize(group.size)}
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
