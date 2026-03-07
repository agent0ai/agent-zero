import { api } from '../client'

export interface ChannelStatus {
  channel: string
  connected: boolean
  enabled: boolean
  error: string | null
  last_activity: number | null
  message_count: number
}

export interface ChannelConfig {
  channel: string
  config: Record<string, string>
}

export function getGatewayStatus(): Promise<{ channels: ChannelStatus[] }> {
  return api('gateway_status')
}

export function connectChannel(channel: string): Promise<{ ok: boolean }> {
  return api('gateway_connect', { body: { channel } })
}

export function disconnectChannel(channel: string): Promise<{ ok: boolean }> {
  return api('gateway_disconnect', { body: { channel } })
}

export function getChannelConfig(channel: string): Promise<ChannelConfig> {
  return api('gateway_channel_config', { method: 'GET', params: { channel } })
}

export function updateChannelConfig(channel: string, config: Record<string, string>): Promise<{ ok: boolean }> {
  return api('gateway_channel_config', { body: { channel, config } })
}
