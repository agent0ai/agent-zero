'use client'

import { useQuery } from '@tanstack/react-query'
import { getTelemetry } from '@/lib/api/endpoints/telemetry'

export function useTelemetry() {
  return useQuery({
    queryKey: ['telemetry'],
    queryFn: getTelemetry,
    refetchInterval: 10_000,
  })
}
