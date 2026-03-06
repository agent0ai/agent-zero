'use client'

import { useState, useMemo } from 'react'
import { Card, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Puzzle, Plus, Search, Code, FileText } from 'lucide-react'

interface Skill {
  name: string
  category: string
  tier: 'markdown' | 'python'
  source: 'tool' | 'instrument'
}

const KNOWN_SKILLS: Skill[] = [
  { name: 'Code Execution', category: 'Core', tier: 'python', source: 'tool' },
  { name: 'Memory Save', category: 'Core', tier: 'python', source: 'tool' },
  { name: 'Memory Load', category: 'Core', tier: 'python', source: 'tool' },
  { name: 'Search Engine', category: 'Core', tier: 'python', source: 'tool' },
  { name: 'Browser Agent', category: 'Core', tier: 'python', source: 'tool' },
  { name: 'Call Subordinate', category: 'Core', tier: 'python', source: 'tool' },
  { name: 'Email', category: 'Communication', tier: 'python', source: 'tool' },
  { name: 'Email Advanced', category: 'Communication', tier: 'python', source: 'tool' },
  { name: 'Telegram Send', category: 'Communication', tier: 'python', source: 'tool' },
  { name: 'Google Voice SMS', category: 'Communication', tier: 'python', source: 'tool' },
  { name: 'Twilio Voice Call', category: 'Communication', tier: 'python', source: 'tool' },
  { name: 'Workflow Engine', category: 'Automation', tier: 'python', source: 'tool' },
  { name: 'Scheduler', category: 'Automation', tier: 'python', source: 'tool' },
  { name: 'Deployment Orchestrator', category: 'DevOps', tier: 'python', source: 'tool' },
  { name: 'DevOps Deploy', category: 'DevOps', tier: 'python', source: 'tool' },
  { name: 'DevOps Monitor', category: 'DevOps', tier: 'python', source: 'tool' },
  { name: 'Security Audit', category: 'Security', tier: 'python', source: 'tool' },
  { name: 'Code Review', category: 'Development', tier: 'python', source: 'tool' },
  { name: 'Project Scaffold', category: 'Development', tier: 'python', source: 'tool' },
  { name: 'API Design', category: 'Development', tier: 'python', source: 'tool' },
  { name: 'Diagram Architect', category: 'Development', tier: 'python', source: 'tool' },
  { name: 'Analytics ROI Calculator', category: 'Analytics', tier: 'python', source: 'tool' },
  { name: 'Portfolio Manager', category: 'Finance', tier: 'python', source: 'tool' },
  { name: 'Finance Manager', category: 'Finance', tier: 'python', source: 'tool' },
  { name: 'Sales Generator', category: 'Business', tier: 'python', source: 'tool' },
  { name: 'Brand Voice', category: 'Business', tier: 'python', source: 'tool' },
  { name: 'Customer Lifecycle', category: 'Business', tier: 'python', source: 'tool' },
  { name: 'Knowledge Ingest', category: 'Knowledge', tier: 'python', source: 'tool' },
  { name: 'Document Query', category: 'Knowledge', tier: 'python', source: 'tool' },
  { name: 'Research Organize', category: 'Knowledge', tier: 'python', source: 'tool' },
  { name: 'Calendar Hub', category: 'Productivity', tier: 'python', source: 'instrument' },
  { name: 'Life OS', category: 'Productivity', tier: 'python', source: 'instrument' },
  { name: 'AI Ops Agent', category: 'DevOps', tier: 'python', source: 'instrument' },
  { name: 'PMS Hub', category: 'Business', tier: 'python', source: 'instrument' },
  { name: 'YT Download', category: 'Media', tier: 'markdown', source: 'instrument' },
]

const CATEGORIES = [...new Set(KNOWN_SKILLS.map((s) => s.category))].sort()

export default function SkillsPage() {
  const [search, setSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState<string | null>(null)

  const filtered = useMemo(() => {
    return KNOWN_SKILLS.filter((skill) => {
      const matchesSearch = !search || skill.name.toLowerCase().includes(search.toLowerCase())
      const matchesCategory = !activeCategory || skill.category === activeCategory
      return matchesSearch && matchesCategory
    })
  }, [search, activeCategory])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Skills</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">Browse, install, and manage agent skills</p>
        </div>
        <Button size="sm"><Plus className="h-4 w-4" /> Create Skill</Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Total Skills</p>
            <p className="text-2xl font-semibold text-[var(--text-primary)]">{KNOWN_SKILLS.length}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Categories</p>
            <p className="text-2xl font-semibold text-[var(--text-primary)]">{CATEGORIES.length}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Instruments</p>
            <p className="text-2xl font-semibold text-[var(--text-primary)]">
              {KNOWN_SKILLS.filter((s) => s.source === 'instrument').length}
            </p>
          </CardBody>
        </Card>
      </div>

      {/* Search + Filter */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <Input
            placeholder="Search skills..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            icon={<Search className="h-4 w-4" />}
          />
        </div>
        <div className="flex gap-1.5 flex-wrap">
          <button
            onClick={() => setActiveCategory(null)}
            className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
              !activeCategory
                ? 'bg-brand-500 text-white'
                : 'bg-[var(--surface-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
          >
            All
          </button>
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(activeCategory === cat ? null : cat)}
              className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                activeCategory === cat
                  ? 'bg-brand-500 text-white'
                  : 'bg-[var(--surface-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Skill Grid */}
      {filtered.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((skill) => (
            <Card key={skill.name} className="hover:border-brand-500/50 transition-colors cursor-pointer">
              <CardBody>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    {skill.tier === 'python' ? (
                      <Code className="h-4 w-4 text-brand-500" />
                    ) : (
                      <FileText className="h-4 w-4 text-info" />
                    )}
                    <h3 className="font-medium text-sm text-[var(--text-primary)]">{skill.name}</h3>
                  </div>
                  <Badge variant={skill.source === 'instrument' ? 'info' : 'neutral'} className="text-[10px]">
                    {skill.source}
                  </Badge>
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <Badge variant="neutral" className="text-[10px]">{skill.category}</Badge>
                  <Badge variant={skill.tier === 'python' ? 'warning' : 'success'} className="text-[10px]">
                    Tier {skill.tier === 'python' ? '2' : '1'}
                  </Badge>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardBody>
            <EmptyState
              icon={<Puzzle className="h-10 w-10" />}
              title="No matching skills"
              description="Try adjusting your search or category filter."
              className="py-8"
            />
          </CardBody>
        </Card>
      )}
    </div>
  )
}
