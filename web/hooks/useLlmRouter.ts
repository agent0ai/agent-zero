'use client'

import { useQuery } from '@tanstack/react-query'
import { getLlmRouterDashboard, getLlmUsage } from '@/lib/api/endpoints/llm-router'

export function useLlmRouter() {
  return useQuery({
    queryKey: ['llm-router'],
    queryFn: getLlmRouterDashboard,
  })
}

export function useLlmUsage() {
  return useQuery({
    queryKey: ['llm-usage'],
    queryFn: getLlmUsage,
  })
}
