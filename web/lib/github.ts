const GITHUB_API_BASE = 'https://api.github.com'
const REPO = process.env.NEXT_PUBLIC_GITHUB_REPO || 'agent-jumbo-deploy/agent-jumbo'

export async function getRepoStats() {
  try {
    const response = await fetch(`${GITHUB_API_BASE}/repos/${REPO}`)
    const data = await response.json()
    return {
      stars: data.stargazers_count || 0,
      forks: data.forks_count || 0,
      watchers: data.watchers_count || 0,
      openIssues: data.open_issues_count || 0,
    }
  } catch (error) {
    console.error('Failed to fetch GitHub stats:', error)
    return {
      stars: 0,
      forks: 0,
      watchers: 0,
      openIssues: 0,
    }
  }
}

export async function getLatestRelease() {
  try {
    const response = await fetch(
      `${GITHUB_API_BASE}/repos/${REPO}/releases/latest`
    )
    const data = await response.json()
    return {
      version: data.tag_name || '1.0.0-beta',
      name: data.name || 'Latest Release',
      published: data.published_at,
    }
  } catch (error) {
    console.error('Failed to fetch release:', error)
    return {
      version: '1.0.0-beta',
      name: 'Latest Release',
      published: new Date().toISOString(),
    }
  }
}
