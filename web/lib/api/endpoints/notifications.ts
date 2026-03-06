import { api } from '../client'

export interface Notification {
  id: string
  type: string
  message: string
  read: boolean
  timestamp: string
}

export function getNotifications(): Promise<{ notifications: Notification[] }> {
  return api('notifications_get')
}

export function markNotificationRead(id: string): Promise<{ ok: boolean }> {
  return api('notification_read', { body: { id } })
}
