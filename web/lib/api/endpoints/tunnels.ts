import { api } from '../client'

export interface TunnelSettings {
  provider: string
  watchdog_interval: number
}

export interface TunnelWatchdogStatus {
  running: boolean
  url: string | null
  provider: string
  last_check: string | null
  error: string | null
}

export interface TunnelStatusResponse {
  settings: TunnelSettings
  watchdog: TunnelWatchdogStatus
}

export function getTunnelSettings(): Promise<TunnelStatusResponse> {
  return api('tunnel_settings_get')
}

export function saveTunnelSettings(settings: Partial<TunnelSettings>): Promise<{ success: boolean }> {
  return api('tunnel_settings_set', { body: { settings } })
}
