'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getTunnelSettings, saveTunnelSettings } from '@/lib/api/endpoints/tunnels'

export function useTunnelSettings() {
  return useQuery({
    queryKey: ['tunnel-settings'],
    queryFn: getTunnelSettings,
    refetchInterval: 15_000,
  })
}

export function useSaveTunnelSettings() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: saveTunnelSettings,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tunnel-settings'] }),
  })
}
