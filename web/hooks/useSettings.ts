'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getSettings, saveSettings } from '@/lib/api/endpoints/settings'

export function useSettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: getSettings,
  })
}

export function useSaveSettings() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: saveSettings,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['settings'] }),
  })
}
