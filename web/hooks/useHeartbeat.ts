'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getHeartbeatConfig,
  updateHeartbeatConfig,
  triggerHeartbeat,
  getHeartbeatLog,
  listHeartbeatTriggers,
  createHeartbeatTrigger,
  updateHeartbeatTrigger,
  deleteHeartbeatTrigger,
  emitHeartbeatEvent,
  type CreateTriggerInput,
  type UpdateTriggerInput,
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

// --- Trigger CRUD hooks ---

export function useHeartbeatTriggers() {
  return useQuery({
    queryKey: ['heartbeat-triggers'],
    queryFn: async () => {
      const data = await listHeartbeatTriggers()
      return data.triggers
    },
    refetchInterval: 30_000,
  })
}

export function useCreateHeartbeatTrigger() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateTriggerInput) => createHeartbeatTrigger(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['heartbeat-triggers'] }),
  })
}

export function useUpdateHeartbeatTrigger() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: UpdateTriggerInput) => updateHeartbeatTrigger(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['heartbeat-triggers'] }),
  })
}

export function useDeleteHeartbeatTrigger() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteHeartbeatTrigger(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['heartbeat-triggers'] }),
  })
}

export function useEmitHeartbeatEvent() {
  return useMutation({
    mutationFn: ({ eventType, payload }: { eventType: string; payload: Record<string, unknown> }) =>
      emitHeartbeatEvent(eventType, payload),
  })
}
