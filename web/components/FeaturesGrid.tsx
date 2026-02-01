import { FEATURES } from '@/lib/constants'

export default function FeaturesGrid() {
  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
            Complete Platform for Intelligent Applications
          </h2>
          <p className="text-xl text-slate-600 dark:text-slate-300">
            Enterprise-grade features for building AI-powered workflows at scale
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {FEATURES.map((feature, index) => (
            <div key={index} className="bg-white dark:bg-slate-800 p-8 rounded-lg border border-slate-200 dark:border-slate-700">
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
                {feature.title}
              </h3>
              <p className="text-slate-600 dark:text-slate-400">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
