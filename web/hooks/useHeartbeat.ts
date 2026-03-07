'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getHeartbeatConfig,
  updateHeartbeatConfig,
  triggerHeartbeat,
  getHeartbeatLog,
} from '@/lib/api/endpoints/heartbeat'

export function useHeartbeatConfig() {
  return useQuery({
    queryKey: ['heartbeat-config'],
    queryFn: getHeartbeatConfig,
    refetchInterval: 15_000,
  })
}

export function useHeartbeatLog() {
  return useQuery({
    queryKey: ['heartbeat-log'],
    queryFn: () => getHeartbeatLog(50),
    refetchInterval: 30_000,
  })
}

export function useUpdateHeartbeat() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: updateHeartbeatConfig,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['heartbeat-config'] }),
  })
}

export function useTriggerHeartbeat() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: triggerHeartbeat,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['heartbeat-config'] })
      qc.invalidateQueries({ queryKey: ['heartbeat-log'] })
    },
  })
}
