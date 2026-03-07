'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listSchedulerTasks,
  createSchedulerTask,
  updateSchedulerTask,
  deleteSchedulerTask,
} from '@/lib/api/endpoints/scheduler'

export function useScheduler() {
  return useQuery({
    queryKey: ['scheduler-tasks'],
    queryFn: listSchedulerTasks,
  })
}

export function useCreateSchedulerTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createSchedulerTask,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scheduler-tasks'] }),
  })
}

export function useUpdateSchedulerTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: updateSchedulerTask,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scheduler-tasks'] }),
  })
}

export function useDeleteSchedulerTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteSchedulerTask,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scheduler-tasks'] }),
  })
}
