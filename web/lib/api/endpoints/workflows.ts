import { api } from '../client'

export interface Workflow {
  id: string
  name: string
  status: string
  steps: Array<{ name: string; status: string }>
  created_at?: string
}

export function getWorkflowDashboard(): Promise<{ workflows: Workflow[] }> {
  return api('workflow_dashboard')
}

export function getWorkflow(id: string): Promise<Workflow> {
  return api('workflow_get', { body: { id } })
}

export function saveWorkflow(workflow: Partial<Workflow>): Promise<{ ok: boolean }> {
  return api('workflow_save', { body: workflow })
}
