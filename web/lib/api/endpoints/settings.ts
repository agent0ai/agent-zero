import { api } from '../client'

export function getSettings(): Promise<Record<string, unknown>> {
  return api('settings_get')
}

export function saveSettings(settings: Record<string, unknown>): Promise<{ ok: boolean }> {
  return api('settings_save', { body: settings })
}
