'use client'

import { useQuery } from '@tanstack/react-query'
import { getGatewayStatus } from '@/lib/api/endpoints/messaging'

export function useGatewayStatus() {
  return useQuery({
    queryKey: ['gateway-status'],
    queryFn: getGatewayStatus,
    refetchInterval: 15_000,
  })
}
