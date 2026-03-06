import { api } from '../client'

export interface HealthResponse {
  ok: boolean
  status: string
  version?: string
  uptime?: number
}

export function healthCheck(): Promise<HealthResponse> {
  return api<HealthResponse>('health_check')
}
