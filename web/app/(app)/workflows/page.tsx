'use client'

import { useState } from 'react'
import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { StatusDot } from '@/components/ui/StatusDot'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { Workflow, Plus, Play, Trash2 } from 'lucide-react'
import { useWorkflows, useSaveWorkflow, useDeleteWorkflow, useRunWorkflow } from '@/hooks/useWorkflows'

const statusVariant: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'neutral'> = {
  running: 'info',
  completed: 'success',
  failed: 'danger',
  paused: 'warning',
  pending: 'neutral',
}

export default function WorkflowsPage() {
  const { data, isLoading } = useWorkflows()
  const workflows = data?.workflows ?? []

  const [modalOpen, setModalOpen] = useState(false)
  const [newName, setNewName] = useState('')

  const saveWorkflow = useSaveWorkflow()
  const deleteWorkflow = useDeleteWorkflow()
  const runWorkflow = useRunWorkflow()

  function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    const name = newName.trim()
    if (!name) return
    saveWorkflow.mutate({ name }, {
      onSuccess: () => {
        setNewName('')
        setModalOpen(false)
      },
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Workflows</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">Build and monitor intelligent workflows</p>
        </div>
        <Button size="sm" onClick={() => setModalOpen(true)}><Plus className="h-4 w-4" /> New Workflow</Button>
      </div>

      <Modal open={modalOpen} onOpenChange={setModalOpen} title="New Workflow" description="Create a new workflow.">
        <form onSubmit={handleCreate} className="space-y-4">
          <Input
            label="Name"
            placeholder="My workflow"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            required
          />
          <div className="flex justify-end gap-2">
            <Button size="sm" variant="secondary" type="button" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button size="sm" type="submit" disabled={saveWorkflow.isPending}>
              {saveWorkflow.isPending ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Total Workflows</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">{workflows.length}</p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Running</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">
                {workflows.filter((w) => w.status === 'running').length}
              </p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Completed</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">
                {workflows.filter((w) => w.status === 'completed').length}
              </p>
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h2 className="font-semibold text-[var(--text-primary)]">All Workflows</h2>
        </CardHeader>
        <CardBody className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-2">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : workflows.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Steps</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workflows.map((wf) => {
                  const completedSteps = wf.steps.filter((s) => s.status === 'completed').length
                  const totalSteps = wf.steps.length
                  const pct = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0

                  return (
                    <TableRow key={wf.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Workflow className="h-3.5 w-3.5 text-[var(--text-tertiary)]" />
                          <span className="font-medium">{wf.name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5">
                          <StatusDot status={statusVariant[wf.status] ?? 'neutral'} pulse={wf.status === 'running'} />
                          <Badge variant={statusVariant[wf.status] ?? 'neutral'}>{wf.status}</Badge>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm text-[var(--text-secondary)]">
                        {completedSteps}/{totalSteps}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-24 rounded-full bg-[var(--surface-tertiary)] overflow-hidden">
                            <div
                              className="h-full rounded-full bg-brand-500 transition-all"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="text-xs text-[var(--text-tertiary)]">{pct}%</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => runWorkflow.mutate(wf.id)}
                            disabled={runWorkflow.isPending}
                          >
                            <Play className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-danger"
                            onClick={() => {
                              if (confirm(`Delete workflow "${wf.name}"?`)) {
                                deleteWorkflow.mutate(wf.id)
                              }
                            }}
                            disabled={deleteWorkflow.isPending}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          ) : (
            <EmptyState
              icon={<Workflow className="h-10 w-10" />}
              title="No workflows yet"
              description="Create your first workflow to automate agent tasks."
              className="py-8"
            />
          )}
        </CardBody>
      </Card>
    </div>
  )
}
