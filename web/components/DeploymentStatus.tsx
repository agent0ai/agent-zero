'use client'

export default function DeploymentStatus() {
  const deployments = [
    {
      name: 'Production API',
      status: 'healthy',
      platform: 'Kubernetes',
      lastDeployed: '2 minutes ago',
    },
    {
      name: 'Staging Web',
      status: 'healthy',
      platform: 'AWS EC2',
      lastDeployed: '1 hour ago',
    },
    {
      name: 'Development Worker',
      status: 'healthy',
      platform: 'SSH',
      lastDeployed: '30 minutes ago',
    },
  ]

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div className="p-6 border-b border-slate-200 dark:border-slate-700">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">
          Recent Deployments
        </h2>
      </div>
      <div className="divide-y divide-slate-200 dark:divide-slate-700">
        {deployments.map((deployment, index) => (
          <div key={index} className="p-6 hover:bg-slate-50 dark:hover:bg-slate-700 transition">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white">
                  {deployment.name}
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                  {deployment.platform} • {deployment.lastDeployed}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-green-600 dark:text-green-400 font-semibold">
                  {deployment.status === 'healthy' ? 'Healthy' : 'Warning'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
