'use client'

import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Puzzle, Plus } from 'lucide-react'

export default function SkillsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Skills</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">Browse, install, and manage agent skills</p>
        </div>
        <Button size="sm"><Plus className="h-4 w-4" /> Create Skill</Button>
      </div>
      <Card>
        <CardHeader>
          <h2 className="font-semibold text-[var(--text-primary)]">Skill Browser</h2>
        </CardHeader>
        <CardBody>
          <EmptyState
            icon={<Puzzle className="h-10 w-10" />}
            title="Skills ecosystem coming soon"
            description="Tier 1 (Markdown) and Tier 2 (Python module) skills will be browsable here."
          />
        </CardBody>
      </Card>
    </div>
  )
}
