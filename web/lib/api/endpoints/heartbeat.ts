import { api } from '../client'

export interface HeartbeatConfigData {
  enabled: boolean
  interval_seconds: number
  heartbeat_path: string
  last_run: string
  run_count: number
  running: boolean
}

export interface HeartbeatRunItem {
  text: string
  completed: boolean
  result: string
  started_at: string
  finished_at: string
}

export interface HeartbeatRun {
  run_id: string
  started_at: string
  finished_at: string
  items: HeartbeatRunItem[]
  status: string
  error: string
}

export function getHeartbeatConfig(): Promise<HeartbeatConfigData> {
  return api('heartbeat_config', { method: 'GET' })
}

export function updateHeartbeatConfig(
  updates: Partial<Pick<HeartbeatConfigData, 'enabled' | 'interval_seconds' | 'heartbeat_path'>>
): Promise<HeartbeatConfigData> {
  return api('heartbeat_config', { body: updates })
}

export function triggerHeartbeat(): Promise<{ status: string; run: HeartbeatRun }> {
  return api('heartbeat_config', { body: { action: 'trigger' } })
}

export function getHeartbeatLog(limit = 50): Promise<{ log: HeartbeatRun[]; count: number }> {
  return api(`heartbeat_log?limit=${limit}`, { method: 'GET' })
}
