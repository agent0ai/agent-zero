import { api } from '../client'

export interface ChannelStatus {
  channel: string
  connected: boolean
  enabled: boolean
  error: string | null
  last_activity: number | null
  message_count: number
}

export function getGatewayStatus(): Promise<{ channels: ChannelStatus[] }> {
  return api('gateway_status')
}
