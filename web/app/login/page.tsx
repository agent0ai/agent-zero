'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardBody } from '@/components/ui/Card'
import { Lock } from 'lucide-react'

export default function LoginPage() {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const res = await fetch('/api/backend/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })

      if (res.ok) {
        window.location.href = '/overview'
      } else {
        setError('Invalid password')
      }
    } catch {
      setError('Unable to connect to server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--surface-secondary)]">
      <Card className="w-full max-w-sm">
        <CardBody className="p-6">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-brand-100 dark:bg-brand-900/30 mb-3">
              <Lock className="h-6 w-6 text-brand-600 dark:text-brand-400" />
            </div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]">Agent Jumbo</h1>
            <p className="text-sm text-[var(--text-secondary)] mt-1">Sign in to continue</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              type="password"
              label="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={error}
              placeholder="Enter your password"
              icon={<Lock className="h-4 w-4" />}
            />
            <Button type="submit" className="w-full" loading={loading}>
              Sign In
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  )
}
