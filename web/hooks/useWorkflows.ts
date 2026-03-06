'use client'

import { useQuery } from '@tanstack/react-query'
import { getWorkflowDashboard } from '@/lib/api/endpoints/workflows'

export function useWorkflows() {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: getWorkflowDashboard,
  })
}
