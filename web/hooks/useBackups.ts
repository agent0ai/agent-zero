'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api/client'

export interface BackupPreviewGroup {
  category: string
  items: string[]
  size?: number
}

export function useBackupPreview() {
  return useQuery({
    queryKey: ['backup-preview'],
    queryFn: () =>
      api<{ data: { groups: BackupPreviewGroup[] } }>('backup_preview_grouped'),
  })
}

export function useCreateBackup() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (name?: string) =>
      api<{ ok: boolean }>('backup_create', { body: { name } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['backup-preview'] }),
  })
}

export function useRestoreBackup() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { id: string }) =>
      api<{ ok: boolean }>('backup_restore', { body: data }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['backup-preview'] })
    },
  })
}
