import { api } from '../client'

export interface SchedulerTask {
  id: string
  name: string
  cron: string
  enabled: boolean
  last_run?: string
  last_result?: string
  next_run?: string
}

export function listSchedulerTasks(): Promise<{ tasks: SchedulerTask[] }> {
  return api('scheduler_tasks_list')
}

export function createSchedulerTask(task: Partial<SchedulerTask>): Promise<{ ok: boolean; id: string }> {
  return api('scheduler_task_create', { body: task })
}

export function updateSchedulerTask(task: Partial<SchedulerTask>): Promise<{ ok: boolean }> {
  return api('scheduler_task_update', { body: task })
}

export function deleteSchedulerTask(id: string): Promise<{ ok: boolean }> {
  return api('scheduler_task_delete', { body: { id } })
}
