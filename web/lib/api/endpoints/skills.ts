import { api } from '../client'

export type TrustLevel = 'builtin' | 'verified' | 'community' | 'local'
export type SkillTier = 'markdown' | 'python'

export interface Skill {
  name: string
  version: string
  author: string
  description: string
  category: string
  tier: SkillTier
  trust_level: TrustLevel
  enabled: boolean
  installed: boolean
  source: 'tool' | 'instrument'
  capabilities: string[]
}

export interface ScanResult {
  name: string
  safe: boolean
  issues: ScanIssue[]
  scanned_at: string
}

export interface ScanIssue {
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  file: string
  line: number
}

export function fetchSkills(): Promise<{ skills: Skill[] }> {
  return api('skills_list', { method: 'GET' })
}

export function fetchSkill(name: string): Promise<Skill> {
  return api('skills_get', { method: 'GET', params: { name } })
}

export function installSkill(nameOrPath: string): Promise<{ ok: boolean }> {
  return api('skills_install', { body: { name_or_path: nameOrPath } })
}

export function uninstallSkill(name: string): Promise<{ ok: boolean }> {
  return api('skills_uninstall', { body: { name } })
}

export function toggleSkill(name: string, enabled: boolean): Promise<{ ok: boolean }> {
  return api('skills_toggle', { body: { name, enabled } })
}

export function scanSkill(nameOrPath: string): Promise<ScanResult> {
  return api('skills_scan', { body: { name_or_path: nameOrPath } })
}

export function searchSkills(query: string): Promise<{ results: Skill[] }> {
  return api('skills_search', { method: 'GET', params: { query } })
}
