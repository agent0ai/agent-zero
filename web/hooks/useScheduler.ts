'use client'

import { useQuery } from '@tanstack/react-query'
import { listSchedulerTasks } from '@/lib/api/endpoints/scheduler'

export function useScheduler() {
  return useQuery({
    queryKey: ['scheduler-tasks'],
    queryFn: listSchedulerTasks,
  })
}
