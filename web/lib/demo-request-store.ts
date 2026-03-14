import { existsSync, promises as fs } from 'fs'
import path from 'path'

type JsonRecord = Record<string, unknown>

function resolveStorePath(): string {
  if (process.env.AGENT_JUMBO_DEMO_REQUESTS_PATH) {
    return process.env.AGENT_JUMBO_DEMO_REQUESTS_PATH
  }

  const cwd = process.cwd()
  const candidates = [
    path.resolve(cwd, 'tmp', 'demo_requests.jsonl'),
    path.resolve(cwd, '..', 'tmp', 'demo_requests.jsonl'),
  ]

  for (const candidate of candidates) {
    if (existsSync(path.dirname(candidate))) return candidate
  }
  return candidates[0]
}

export async function appendDemoRequest(data: JsonRecord): Promise<JsonRecord> {
  const filePath = resolveStorePath()
  await fs.mkdir(path.dirname(filePath), { recursive: true })

  const record: JsonRecord = {
    id: `dr_${Math.random().toString(36).slice(2, 14)}`,
    created_at: new Date().toISOString(),
    ...data,
  }
  await fs.appendFile(filePath, `${JSON.stringify(record)}\n`, 'utf8')
  return record
}

export async function listDemoRequests(limit = 25): Promise<JsonRecord[]> {
  const filePath = resolveStorePath()
  try {
    const content = await fs.readFile(filePath, 'utf8')
    const rows = content
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        try {
          return JSON.parse(line) as JsonRecord
        } catch {
          return null
        }
      })
      .filter((row): row is JsonRecord => row !== null)
    return rows.slice(-Math.max(limit, 1)).reverse()
  } catch {
    return []
  }
}
