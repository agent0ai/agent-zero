import { api } from '../client'

export interface TelemetryEvent {
  timestamp: string
  type: string
  data: Record<string, unknown>
}

export function getTelemetry(): Promise<{ events: TelemetryEvent[] }> {
  return api('telemetry_get')
}
