'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { pollChat, type ChatLog, type ChatContext, type PollResponse } from '@/lib/api/endpoints/chat'

interface RealtimeState {
  logs: ChatLog[]
  contexts: ChatContext[]
  progress: string
  progressActive: boolean
  paused: boolean
  connected: boolean
}

export function useRealtime(contextId: string | null, enabled = true) {
  const [state, setState] = useState<RealtimeState>({
    logs: [],
    contexts: [],
    progress: '',
    progressActive: false,
    paused: false,
    connected: false,
  })

  const logVersionRef = useRef(0)
  const logGuidRef = useRef('')
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const doPoll = useCallback(async () => {
    if (!enabled) return
    try {
      const data: PollResponse = await pollChat(contextId, logVersionRef.current)

      // Handle log_guid change (context reset)
      if (logGuidRef.current && logGuidRef.current !== data.log_guid) {
        logVersionRef.current = 0
        logGuidRef.current = data.log_guid
        setState((prev) => ({ ...prev, logs: [] }))
        // Re-poll with version 0
        const fresh = await pollChat(contextId, 0)
        logVersionRef.current = fresh.log_version
        setState((prev) => ({
          ...prev,
          logs: fresh.logs,
          contexts: fresh.contexts,
          progress: fresh.log_progress,
          progressActive: fresh.log_progress_active,
          paused: fresh.paused,
          connected: true,
        }))
        return
      }

      logGuidRef.current = data.log_guid

      if (data.log_version !== logVersionRef.current) {
        setState((prev) => ({
          ...prev,
          logs: logVersionRef.current === 0 ? data.logs : [...prev.logs, ...data.logs],
          contexts: data.contexts,
          progress: data.log_progress,
          progressActive: data.log_progress_active,
          paused: data.paused,
          connected: true,
        }))
        logVersionRef.current = data.log_version
      } else {
        setState((prev) => ({
          ...prev,
          contexts: data.contexts,
          progress: data.log_progress,
          progressActive: data.log_progress_active,
          paused: data.paused,
          connected: true,
        }))
      }
    } catch {
      setState((prev) => ({ ...prev, connected: false }))
    }
  }, [contextId, enabled])

  // Reset on context change
  useEffect(() => {
    logVersionRef.current = 0
    logGuidRef.current = ''
    setState((prev) => ({ ...prev, logs: [] }))
  }, [contextId])

  // Polling interval
  useEffect(() => {
    if (!enabled) return

    doPoll()
    intervalRef.current = setInterval(doPoll, 1500)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [doPoll, enabled])

  return state
}
