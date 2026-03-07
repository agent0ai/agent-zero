'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getWorkflowDashboard,
  saveWorkflow,
  deleteWorkflow,
  runWorkflow,
} from '@/lib/api/endpoints/workflows'

export function useWorkflows() {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: getWorkflowDashboard,
  })
}

export function useSaveWorkflow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: saveWorkflow,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workflows'] }),
  })
}

export function useDeleteWorkflow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteWorkflow,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workflows'] }),
  })
}

export function useRunWorkflow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: runWorkflow,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workflows'] }),
  })
}
