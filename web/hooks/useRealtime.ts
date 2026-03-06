'use client'

import { useQuery } from '@tanstack/react-query'
import { pollChat, type PollResponse } from '@/lib/api/endpoints/chat'

export function useRealtime(contextId: string | null, enabled = true) {
  return useQuery<PollResponse>({
    queryKey: ['poll', contextId],
    queryFn: () => pollChat(contextId!),
    enabled: enabled && !!contextId,
    refetchInterval: 1500,
    refetchIntervalInBackground: false,
  })
}
