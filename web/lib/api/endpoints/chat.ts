import { api } from '../client'

export interface ChatMessage {
  type: string
  heading?: string
  content: string
  kvps?: Record<string, unknown>
}

export interface PollResponse {
  ok: boolean
  logs: ChatMessage[]
  log_progress: string
  contexts: Array<{ id: string; name: string; log_length: number }>
  tasks: Array<{ id: string; status: string; description: string }>
  notifications: Array<{ type: string; message: string }>
}

export function pollChat(contextId: string): Promise<PollResponse> {
  return api<PollResponse>('poll', { body: { context: contextId } })
}

export function sendMessage(text: string, contextId: string, attachments: string[] = []): Promise<{ ok: boolean }> {
  return api('message', { body: { text, context: contextId, attachments } })
}

export function createChat(): Promise<{ context: string }> {
  return api('chat_create')
}

export function resetChat(contextId: string): Promise<{ ok: boolean }> {
  return api('chat_reset', { body: { context: contextId } })
}
