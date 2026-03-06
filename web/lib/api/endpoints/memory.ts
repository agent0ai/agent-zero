import { api } from '../client'

export function getMemoryDashboard(): Promise<{ memories: Array<Record<string, unknown>> }> {
  return api('memory_dashboard')
}
