'use client'

import { useState, useMemo } from 'react'
import { Card, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Skeleton } from '@/components/ui/Skeleton'
import { Puzzle, Plus, Search } from 'lucide-react'
import { SkillCard } from '@/components/skills/SkillCard'
import { SkillDetail } from '@/components/skills/SkillDetail'
import { useSkills, useInstallSkill, useUninstallSkill, useToggleSkill } from '@/hooks/useSkills'
import type { Skill } from '@/lib/api/endpoints/skills'

/** Fallback data when the backend is not reachable */
const FALLBACK_SKILLS: Skill[] = [
  { name: 'Code Execution', category: 'Core', tier: 'python', source: 'tool', trust_level: 'builtin', version: '1.0.0', author: 'Agent Jumbo', description: 'Execute code in sandboxed environments', enabled: true, installed: true, capabilities: ['python', 'node', 'bash'] },
  { name: 'Memory Save', category: 'Core', tier: 'python', source: 'tool', trust_level: 'builtin', version: '1.0.0', author: 'Agent Jumbo', description: 'Save context to persistent memory', enabled: true, installed: true, capabilities: ['write'] },
  { name: 'Memory Load', category: 'Core', tier: 'python', source: 'tool', trust_level: 'builtin', version: '1.0.0', author: 'Agent Jumbo', description: 'Load context from persistent memory', enabled: true, installed: true, capabilities: ['read'] },
  { name: 'Search Engine', category: 'Core', tier: 'python', source: 'tool', trust_level: 'builtin', version: '1.0.0', author: 'Agent Jumbo', description: 'Web search integration', enabled: true, installed: true, capabilities: ['search'] },
  { name: 'Browser Agent', category: 'Core', tier: 'python', source: 'tool', trust_level: 'builtin', version: '1.0.0', author: 'Agent Jumbo', description: 'Automated browser interaction', enabled: true, installed: true, capabilities: ['browse', 'scrape'] },
  { name: 'Call Subordinate', category: 'Core', tier: 'python', source: 'tool', trust_level: 'builtin', version: '1.0.0', author: 'Agent Jumbo', description: 'Delegate tasks to sub-agents', enabled: true, installed: true, capabilities: ['delegation'] },
  { name: 'Email', category: 'Communication', tier: 'python', source: 'tool', trust_level: 'verified', version: '1.0.0', author: 'Agent Jumbo', description: 'Send and receive emails', enabled: true, installed: true, capabilities: ['send', 'receive'] },
  { name: 'Telegram Send', category: 'Communication', tier: 'python', source: 'tool', trust_level: 'verified', version: '1.0.0', author: 'Agent Jumbo', description: 'Send Telegram messages', enabled: true, installed: true, capabilities: ['send'] },
  { name: 'Workflow Engine', category: 'Automation', tier: 'python', source: 'tool', trust_level: 'builtin', version: '1.0.0', author: 'Agent Jumbo', description: 'Multi-step workflow orchestration', enabled: true, installed: true, capabilities: ['orchestrate'] },
  { name: 'Scheduler', category: 'Automation', tier: 'python', source: 'tool', trust_level: 'builtin', version: '1.0.0', author: 'Agent Jumbo', description: 'Schedule recurring tasks', enabled: true, installed: true, capabilities: ['cron', 'schedule'] },
  { name: 'Deployment Orchestrator', category: 'DevOps', tier: 'python', source: 'tool', trust_level: 'verified', version: '1.0.0', author: 'Agent Jumbo', description: 'Orchestrate deployments', enabled: true, installed: true, capabilities: ['deploy'] },
  { name: 'Security Audit', category: 'Security', tier: 'python', source: 'tool', trust_level: 'builtin', version: '1.0.0', author: 'Agent Jumbo', description: 'Security scanning and auditing', enabled: true, installed: true, capabilities: ['scan', 'audit'] },
  { name: 'Code Review', category: 'Development', tier: 'python', source: 'tool', trust_level: 'verified', version: '1.0.0', author: 'Agent Jumbo', description: 'Automated code review', enabled: true, installed: true, capabilities: ['review'] },
  { name: 'Knowledge Ingest', category: 'Knowledge', tier: 'python', source: 'tool', trust_level: 'builtin', version: '1.0.0', author: 'Agent Jumbo', description: 'Ingest documents into knowledge base', enabled: true, installed: true, capabilities: ['ingest'] },
  { name: 'Calendar Hub', category: 'Productivity', tier: 'python', source: 'instrument', trust_level: 'community', version: '0.9.0', author: 'Community', description: 'Calendar management instrument', enabled: true, installed: true, capabilities: ['calendar'] },
  { name: 'YT Download', category: 'Media', tier: 'markdown', source: 'instrument', trust_level: 'community', version: '0.5.0', author: 'Community', description: 'YouTube video downloader', enabled: false, installed: true, capabilities: ['download'] },
]

export default function SkillsPage() {
  const [search, setSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState<string | null>(null)
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)

  const { data: apiSkills, isLoading } = useSkills()
  const installMutation = useInstallSkill()
  const uninstallMutation = useUninstallSkill()
  const toggleMutation = useToggleSkill()

  const skills = apiSkills ?? FALLBACK_SKILLS

  const categories = useMemo(() => {
    return [...new Set(skills.map((s) => s.category))].sort()
  }, [skills])

  const filtered = useMemo(() => {
    return skills.filter((skill) => {
      const matchesSearch = !search || skill.name.toLowerCase().includes(search.toLowerCase())
      const matchesCategory = !activeCategory || skill.category === activeCategory
      return matchesSearch && matchesCategory
    })
  }, [skills, search, activeCategory])

  const enabledCount = skills.filter((s) => s.enabled).length
  const instrumentCount = skills.filter((s) => s.source === 'instrument').length

  const handleCardClick = (skill: Skill) => {
    setSelectedSkill(skill.name)
    setDetailOpen(true)
  }

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
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Total Skills</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">{skills.length}</p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Enabled</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">{enabledCount}</p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Categories</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">{categories.length}</p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-xs text-[var(--text-secondary)]">Instruments</p>
            {isLoading ? (
              <Skeleton className="h-7 w-12 mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-[var(--text-primary)]">{instrumentCount}</p>
            )}
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
          {categories.map((cat) => (
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
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 9 }).map((_, i) => (
            <Card key={i}>
              <CardBody>
                <Skeleton className="h-24 w-full" />
              </CardBody>
            </Card>
          ))}
        </div>
      ) : filtered.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((skill) => (
            <SkillCard
              key={skill.name}
              skill={skill}
              onClick={() => handleCardClick(skill)}
              onToggle={(enabled) => toggleMutation.mutate({ name: skill.name, enabled })}
              onInstall={!skill.installed ? () => installMutation.mutate(skill.name) : undefined}
              onUninstall={skill.installed ? () => uninstallMutation.mutate(skill.name) : undefined}
              isToggling={toggleMutation.isPending}
              isInstalling={installMutation.isPending}
            />
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

      {/* Skill Detail Modal */}
      <SkillDetail
        skillName={selectedSkill}
        open={detailOpen}
        onOpenChange={setDetailOpen}
      />
    </div>
  )
}
