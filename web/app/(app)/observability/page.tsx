'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { Eye, Clock } from 'lucide-react'
import { useTelemetry } from '@/hooks/useTelemetry'
import { format } from 'date-fns'

export default function ObservabilityPage() {
  const { data, isLoading } = useTelemetry()
  const events = data?.events ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Observability</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">Telemetry, logs, and event timeline</p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Total Events</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">{events.length}</p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Event Types</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">
                {new Set(events.map((e) => e.type)).size}
              </p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Latest Event</p>
            {isLoading ? (
              <Skeleton className="h-7 w-24 mt-1" />
            ) : (
              <p className="text-sm font-medium text-[var(--text-primary)] mt-1">
                {events.length > 0
                  ? format(new Date(events[events.length - 1].timestamp), 'HH:mm:ss')
                  : 'None'}
              </p>
            )}
          </CardBody>
        </Card>
      </div>

      <Tabs defaultValue="events">
        <TabsList>
          <TabsTrigger value="events">Event Log</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
        </TabsList>

        <TabsContent value="events">
          <Card>
            <CardHeader>
              <h2 className="font-semibold text-[var(--text-primary)]">Telemetry Events</h2>
            </CardHeader>
            <CardBody className="p-0">
              {isLoading ? (
                <div className="p-4 space-y-2">
                  {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
                </div>
              ) : events.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Time</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Details</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {events.slice(-50).reverse().map((event, i) => (
                      <TableRow key={i}>
                        <TableCell className="whitespace-nowrap">
                          <div className="flex items-center gap-1.5 text-xs">
                            <Clock className="h-3 w-3 text-[var(--text-tertiary)]" />
                            {format(new Date(event.timestamp), 'HH:mm:ss')}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="info">{event.type}</Badge>
                        </TableCell>
                        <TableCell>
                          <pre className="text-xs text-[var(--text-secondary)] max-w-md truncate">
                            {JSON.stringify(event.data)}
                          </pre>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <EmptyState
                  icon={<Eye className="h-10 w-10" />}
                  title="No telemetry events"
                  description="Events will appear here once the backend is connected and processing requests."
                  className="py-8"
                />
              )}
            </CardBody>
          </Card>
        </TabsContent>

        <TabsContent value="timeline">
          <Card>
            <CardHeader>
              <h2 className="font-semibold text-[var(--text-primary)]">Telemetry Timeline</h2>
            </CardHeader>
            <CardBody>
              {events.length > 0 ? (
                <div className="space-y-2">
                  {events.slice(-20).reverse().map((event, i) => (
                    <div key={i} className="flex items-start gap-3 text-sm">
                      <div className="shrink-0 mt-1">
                        <div className="h-2 w-2 rounded-full bg-brand-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <Badge variant="info" className="text-[10px]">{event.type}</Badge>
                          <span className="text-xs text-[var(--text-tertiary)]">
                            {format(new Date(event.timestamp), 'MMM d, HH:mm:ss')}
                          </span>
                        </div>
                        <p className="text-xs text-[var(--text-secondary)] mt-0.5 truncate">
                          {JSON.stringify(event.data)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={<Eye className="h-10 w-10" />}
                  title="No timeline data"
                  description="Telemetry events from telemetry_get will render as a timeline here."
                />
              )}
            </CardBody>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
