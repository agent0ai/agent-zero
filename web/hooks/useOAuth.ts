'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listGmailAccounts, removeGmailAccount, startGmailOAuth } from '@/lib/api/endpoints/oauth'

export function useGmailAccounts() {
  return useQuery({
    queryKey: ['gmail-accounts'],
    queryFn: listGmailAccounts,
  })
}

export function useRemoveGmailAccount() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: removeGmailAccount,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gmail-accounts'] }),
  })
}

export function useStartGmailOAuth() {
  return useMutation({
    mutationFn: startGmailOAuth,
  })
}
