'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { sendMessage, createChat, resetChat } from '@/lib/api/endpoints/chat'

export function useSendMessage(contextId: string | null) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (text: string) => {
      if (!contextId) throw new Error('No context selected')
      return sendMessage(text, contextId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['poll', contextId] })
    },
  })
}

export function useCreateChat() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => createChat(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['poll'] })
    },
  })
}

export function useResetChat() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (contextId: string) => resetChat(contextId),
    onSuccess: (_, contextId) => {
      queryClient.invalidateQueries({ queryKey: ['poll', contextId] })
    },
  })
}
