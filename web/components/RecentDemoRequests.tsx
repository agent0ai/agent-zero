'use client'

import { type FormEvent, useEffect, useState } from 'react'

interface DemoRequest {
  id: string
  created_at?: string
  company?: string
  email?: string
  industry?: string
  teamSize?: string
}

interface DemoRequestsResponse {
  success: boolean
  count: number
  requests: DemoRequest[]
}

function formatDate(value?: string): string {
  if (!value) return 'Unknown'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString()
}

export default function RecentDemoRequests() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [requests, setRequests] = useState<DemoRequest[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [submitMessage, setSubmitMessage] = useState<string | null>(null)
  const [form, setForm] = useState({
    company: '',
    email: '',
    industry: '',
    teamSize: '',
  })

  async function loadRequests() {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/demo-request?limit=10')
      if (!response.ok) {
        throw new Error(`Request failed (${response.status})`)
      }

      const data = (await response.json()) as DemoRequestsResponse
      setRequests(Array.isArray(data.requests) ? data.requests : [])
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load requests'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let active = true

    async function run() {
      if (!active) return
      await loadRequests()
    }

    run()
    return () => {
      active = false
    }
  }, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setSubmitMessage(null)

    try {
      const response = await fetch('/api/demo-request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const data = (await response.json()) as { success?: boolean; message?: string; error?: string }
      if (!response.ok || !data.success) {
        throw new Error(data.error || data.message || `Request failed (${response.status})`)
      }

      setSubmitMessage('Demo request created.')
      setForm({
        company: '',
        email: '',
        industry: '',
        teamSize: '',
      })
      await loadRequests()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create request'
      setSubmitMessage(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div className="p-6 border-b border-slate-200 dark:border-slate-700">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">
          Recent Demo Requests
        </h2>
        <form onSubmit={handleSubmit} className="mt-4 grid gap-3 md:grid-cols-4">
          <input
            type="text"
            value={form.company}
            onChange={(e) => setForm((prev) => ({ ...prev, company: e.target.value }))}
            required
            placeholder="Company"
            className="px-3 py-2 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
          />
          <input
            type="email"
            value={form.email}
            onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
            required
            placeholder="Email"
            className="px-3 py-2 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
          />
          <input
            type="text"
            value={form.industry}
            onChange={(e) => setForm((prev) => ({ ...prev, industry: e.target.value }))}
            placeholder="Industry (optional)"
            className="px-3 py-2 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
          />
          <div className="flex gap-2">
            <input
              type="text"
              value={form.teamSize}
              onChange={(e) => setForm((prev) => ({ ...prev, teamSize: e.target.value }))}
              placeholder="Team size"
              className="w-full px-3 py-2 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
            />
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {submitting ? 'Saving...' : 'Create'}
            </button>
          </div>
        </form>
        {submitMessage && (
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">{submitMessage}</p>
        )}
      </div>

      {loading && (
        <div className="p-6 text-slate-600 dark:text-slate-300">Loading demo requests...</div>
      )}

      {!loading && error && (
        <div className="p-6 text-red-600 dark:text-red-400">
          Could not load demo requests: {error}
        </div>
      )}

      {!loading && !error && requests.length === 0 && (
        <div className="p-6 text-slate-600 dark:text-slate-300">No demo requests yet.</div>
      )}

      {!loading && !error && requests.length > 0 && (
        <div className="divide-y divide-slate-200 dark:divide-slate-700">
          {requests.map((request) => (
            <div key={request.id} className="p-6 hover:bg-slate-50 dark:hover:bg-slate-700 transition">
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <p className="font-semibold text-slate-900 dark:text-white">
                    {request.company || 'Unknown Company'}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {formatDate(request.created_at)}
                  </p>
                </div>
                <p className="text-sm text-slate-700 dark:text-slate-200">{request.email || 'No email'}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {request.industry || 'Industry n/a'} • {request.teamSize || 'Team size n/a'} • {request.id}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
