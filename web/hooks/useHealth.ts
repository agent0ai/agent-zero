'use client'

import { useQuery } from '@tanstack/react-query'
import { healthCheck, type HealthResponse } from '@/lib/api/endpoints/health'

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: healthCheck,
    refetchInterval: 30_000,
    retry: 1,
  })
}
