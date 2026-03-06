'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { StatusDot } from '@/components/ui/StatusDot'
import { Button } from '@/components/ui/Button'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { Calendar, Plus, Clock } from 'lucide-react'
import { useScheduler } from '@/hooks/useScheduler'
import { format } from 'date-fns'

export default function SchedulerPage() {
  const { data, isLoading } = useScheduler()
  const tasks = data?.tasks ?? []

  const enabledCount = tasks.filter((t) => t.enabled).length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Scheduler</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">Schedule recurring agent tasks with cron expressions</p>
        </div>
        <Button size="sm"><Plus className="h-4 w-4" /> New Task</Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Total Tasks</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">{tasks.length}</p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Active</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">{enabledCount}</p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Disabled</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">{tasks.length - enabledCount}</p>
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h2 className="font-semibold text-[var(--text-primary)]">Scheduled Tasks</h2>
        </CardHeader>
        <CardBody className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-2">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : tasks.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Cron</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Run</TableHead>
                  <TableHead>Next Run</TableHead>
                  <TableHead>Last Result</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tasks.map((task) => (
                  <TableRow key={task.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Calendar className="h-3.5 w-3.5 text-[var(--text-tertiary)]" />
                        <span className="font-medium">{task.name}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="text-xs bg-[var(--surface-tertiary)] px-1.5 py-0.5 rounded font-mono">
                        {task.cron}
                      </code>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <StatusDot status={task.enabled ? 'success' : 'neutral'} pulse={task.enabled} />
                        <span className="text-sm">{task.enabled ? 'Active' : 'Disabled'}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {task.last_run ? (
                        <div className="flex items-center gap-1 text-xs text-[var(--text-secondary)]">
                          <Clock className="h-3 w-3" />
                          {format(new Date(task.last_run), 'MMM d, HH:mm')}
                        </div>
                      ) : (
                        <span className="text-xs text-[var(--text-tertiary)]">Never</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {task.next_run ? (
                        <span className="text-xs text-[var(--text-secondary)]">
                          {format(new Date(task.next_run), 'MMM d, HH:mm')}
                        </span>
                      ) : (
                        <span className="text-xs text-[var(--text-tertiary)]">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {task.last_result ? (
                        <Badge variant={task.last_result === 'success' ? 'success' : task.last_result === 'error' ? 'danger' : 'neutral'}>
                          {task.last_result}
                        </Badge>
                      ) : (
                        <span className="text-xs text-[var(--text-tertiary)]">—</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <EmptyState
              icon={<Calendar className="h-10 w-10" />}
              title="No scheduled tasks"
              description="Create a scheduled task to run agents on a cron schedule."
              className="py-8"
            />
          )}
        </CardBody>
      </Card>
    </div>
  )
}
