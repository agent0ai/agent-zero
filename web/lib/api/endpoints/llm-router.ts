import { api } from '../client'

export interface LlmModel {
  id: string
  provider: string
  name: string
  enabled: boolean
}

export interface LlmUsage {
  model: string
  tokens: number
  cost: number
  requests: number
}

export function getLlmRouterDashboard(): Promise<{ models: LlmModel[]; usage: LlmUsage[] }> {
  return api('llm_router_dashboard')
}

export function getLlmUsage(): Promise<{ usage: LlmUsage[] }> {
  return api('llm_router_usage')
}

export function getLlmRules(): Promise<{ rules: Array<Record<string, unknown>> }> {
  return api('llm_router_rules')
}

export function discoverModels(): Promise<{ models: LlmModel[] }> {
  return api('llm_router_discover')
}
