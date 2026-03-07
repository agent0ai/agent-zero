'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getWorkDirFiles, deleteWorkDirFile } from '@/lib/api/endpoints/files'

export function useFiles(path: string) {
  return useQuery({
    queryKey: ['files', path],
    queryFn: () => getWorkDirFiles(path),
  })
}

export function useDeleteFile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteWorkDirFile,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['files'] }),
  })
}
