'use client'

import { useQuery } from '@tanstack/react-query'
import { getMemoryDashboard } from '@/lib/api/endpoints/memory'

export function useMemoryDashboard() {
  return useQuery({
    queryKey: ['memory-dashboard'],
    queryFn: getMemoryDashboard,
    refetchInterval: 30_000,
  })
}
