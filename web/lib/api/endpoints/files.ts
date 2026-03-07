import { api } from '../client'

export interface FileEntry {
  name: string
  path: string
  type: 'file' | 'directory'
  size?: number
  modified?: string
}

export interface FileBrowserResult {
  data: {
    files: FileEntry[]
    current_path: string
    parent_path: string | null
  }
}

export function getWorkDirFiles(path = ''): Promise<FileBrowserResult> {
  return api('get_work_dir_files', {
    method: 'GET',
    params: { path },
  })
}

export function deleteWorkDirFile(path: string): Promise<{ ok: boolean }> {
  return api('delete_work_dir_file', { body: { path } })
}
