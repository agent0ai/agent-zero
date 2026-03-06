import { api } from '../client'

export interface Backup {
  id: string
  name: string
  size: number
  created_at: string
}

export function listBackups(): Promise<{ backups: Backup[] }> {
  return api('backup_list')
}

export function createBackup(): Promise<{ ok: boolean; id: string }> {
  return api('backup_create')
}

export function restoreBackup(id: string): Promise<{ ok: boolean }> {
  return api('backup_restore', { body: { id } })
}
