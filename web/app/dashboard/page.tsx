'use client'

import DashboardLayout from '@/components/DashboardLayout'
import QuickStats from '@/components/QuickStats'
import DeploymentStatus from '@/components/DeploymentStatus'
import RecentDemoRequests from '@/components/RecentDemoRequests'

export default function Dashboard() {
  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
            Deployment Dashboard
          </h1>
          <p className="text-slate-600 dark:text-slate-300">
            Monitor and manage your deployments across all platforms
          </p>
        </div>

        <QuickStats />
        <DeploymentStatus />
        <RecentDemoRequests />
      </div>
    </DashboardLayout>
  )
}
