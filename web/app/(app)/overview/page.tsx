'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { StatusDot } from '@/components/ui/StatusDot'
import { Activity, Cpu, Rocket, Clock } from 'lucide-react'

const stats = [
  { label: 'Active Agents', value: '--', icon: Cpu, color: 'text-brand-500' },
  { label: 'Deployments', value: '--', icon: Rocket, color: 'text-success' },
  { label: 'Success Rate', value: '--', icon: Activity, color: 'text-info' },
  { label: 'Avg Response', value: '--', icon: Clock, color: 'text-warning' },
]

export default function OverviewPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Overview</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          System health and activity summary
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.label}>
              <CardBody>
                <div className="flex items-center gap-3">
                  <div className={`${stat.color}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-xs text-[var(--text-secondary)]">{stat.label}</p>
                    <p className="text-xl font-semibold text-[var(--text-primary)]">{stat.value}</p>
                  </div>
                </div>
              </CardBody>
            </Card>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-[var(--text-primary)]">System Health</h2>
              <Badge variant="success">Operational</Badge>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {['Flask API', 'Agent Runtime', 'Memory Store', 'Task Scheduler'].map((svc) => (
                <div key={svc} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <StatusDot status="success" />
                    <span className="text-[var(--text-primary)]">{svc}</span>
                  </div>
                  <span className="text-[var(--text-secondary)]">Healthy</span>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="font-semibold text-[var(--text-primary)]">Recent Activity</h2>
          </CardHeader>
          <CardBody>
            <p className="text-sm text-[var(--text-tertiary)] text-center py-8">
              Connect to the backend to see live activity
            </p>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
