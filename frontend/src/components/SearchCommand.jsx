import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, FolderKanban, Ticket } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'

export default function SearchCommand({ open, onOpenChange }) {
  const navigate = useNavigate()
  const { authFetch } = useAuth()
  const [query, setQuery] = useState('')
  const [projects, setProjects] = useState([])
  const [issues, setIssues] = useState([])

  useEffect(() => {
    const down = (e) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        onOpenChange((open) => !open)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [onOpenChange])

  useEffect(() => {
    if (!open) {
      setQuery('')
      setProjects([])
      setIssues([])
      return
    }

    authFetch('/api/v1/teams')
      .then((r) => (r.ok ? r.json() : []))
      .then((teams) => {
        if (teams.length > 0) {
          return authFetch(`/api/v1/projects/team/${teams[0].slug}`)
        }
        return { json: () => [] }
      })
      .then((r) => r.json())
      .then(setProjects)
  }, [open, authFetch])

  useEffect(() => {
    if (!query.trim() || projects.length === 0) {
      setIssues([])
      return
    }

    const slug = projects[0]?.slug
    if (!slug) return

    const timer = setTimeout(() => {
      authFetch(`/api/v1/issues/project/${slug}`)
        .then((r) => (r.ok ? r.json() : []))
        .then((data) => {
          const filtered = data.filter((i) =>
            i.title.toLowerCase().includes(query.toLowerCase()) ||
            i.identifier.toLowerCase().includes(query.toLowerCase())
          )
          setIssues(filtered.slice(0, 5))
        })
    }, 200)

    return () => clearTimeout(timer)
  }, [query, projects, authFetch])

  const filteredProjects = projects.filter((p) =>
    p.name.toLowerCase().includes(query.toLowerCase()) ||
    p.slug.toLowerCase().includes(query.toLowerCase())
  ).slice(0, 5)

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput
        placeholder="프로젝트 또는 이슈 검색..."
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        <CommandEmpty>결과가 없습니다.</CommandEmpty>
        {filteredProjects.length > 0 && (
          <CommandGroup heading="프로젝트">
            {filteredProjects.map((p) => (
              <CommandItem
                key={p.id}
                onSelect={() => {
                  navigate(`/projects/${p.slug}`)
                  onOpenChange(false)
                }}
              >
                <FolderKanban className="mr-2 h-4 w-4" />
                {p.name}
                <span className="ml-2 text-xs text-muted-foreground">{p.slug}</span>
              </CommandItem>
            ))}
          </CommandGroup>
        )}
        {issues.length > 0 && (
          <CommandGroup heading="이슈">
            {issues.map((i) => (
              <CommandItem
                key={i.id}
                onSelect={() => {
                  navigate(`/projects/${i.project?.slug || projects[0]?.slug}/issues/${i.identifier}`)
                  onOpenChange(false)
                }}
              >
                <Ticket className="mr-2 h-4 w-4" />
                {i.identifier}: {i.title}
              </CommandItem>
            ))}
          </CommandGroup>
        )}
      </CommandList>
    </CommandDialog>
  )
}
