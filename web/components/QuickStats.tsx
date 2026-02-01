export default function QuickStats() {
  const stats = [
    { label: 'Active Deployments', value: '12', icon: '🚀' },
    { label: 'Success Rate', value: '99.2%', icon: '✅' },
    { label: 'Avg Deploy Time', value: '2.3s', icon: '⏱️' },
    { label: 'Error Recovery Rate', value: '98.7%', icon: '🛡️' },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, index) => (
        <div
          key={index}
          className="bg-white dark:bg-slate-800 p-6 rounded-lg border border-slate-200 dark:border-slate-700"
        >
          <div className="text-3xl mb-2">{stat.icon}</div>
          <p className="text-slate-600 dark:text-slate-400 text-sm mb-1">
            {stat.label}
          </p>
          <p className="text-2xl font-bold text-slate-900 dark:text-white">
            {stat.value}
          </p>
        </div>
      ))}
    </div>
  )
}
