'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import {
  fetchSkills,
  fetchSkill,
  installSkill,
  uninstallSkill,
  toggleSkill,
  scanSkill,
  searchSkills,
} from '@/lib/api/endpoints/skills'

export function useSkills() {
  return useQuery({
    queryKey: ['skills'],
    queryFn: async () => {
      const data = await fetchSkills()
      return data.skills
    },
    refetchInterval: 30_000,
  })
}

export function useSkill(name: string | null) {
  return useQuery({
    queryKey: ['skill', name],
    queryFn: () => fetchSkill(name!),
    enabled: !!name,
  })
}

export function useInstallSkill() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (nameOrPath: string) => installSkill(nameOrPath),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['skills'] }),
  })
}

export function useUninstallSkill() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => uninstallSkill(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['skills'] }),
  })
}

export function useToggleSkill() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ name, enabled }: { name: string; enabled: boolean }) =>
      toggleSkill(name, enabled),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['skills'] }),
  })
}

export function useScanSkill() {
  return useMutation({
    mutationFn: (nameOrPath: string) => scanSkill(nameOrPath),
  })
}

export function useSearchSkills(query: string) {
  const [debouncedQuery, setDebouncedQuery] = useState(query)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300)
    return () => clearTimeout(timer)
  }, [query])

  return useQuery({
    queryKey: ['skills-search', debouncedQuery],
    queryFn: async () => {
      const data = await searchSkills(debouncedQuery)
      return data.results
    },
    enabled: debouncedQuery.length >= 2,
  })
}
