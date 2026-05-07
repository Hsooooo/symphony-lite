import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, FolderKanban } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'

export default function ProjectList() {
  const { user, authFetch } = useAuth()
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ slug: '', name: '', repo_url: '' })
  const [error, setError] = useState('')

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const teamsRes = await authFetch('/api/v1/teams')
      const teams = teamsRes.ok ? await teamsRes.json() : []
      if (teams.length === 0) return []
      const res = await authFetch(`/api/v1/projects/team/${teams[0].slug}`)
      if (!res.ok) return []
      return res.json()
    },
  })

  const createMutation = useMutation({
    mutationFn: async (body) => {
      const res = await authFetch('/api/v1/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || '생성 실패')
      }
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setForm({ slug: '', name: '', repo_url: '' })
      setError('')
      setOpen(false)
    },
    onError: (err) => setError(err.message),
  })

  const handleCreate = (e) => {
    e.preventDefault()
    setError('')
    createMutation.mutate({ ...form, team_id: user?.team_id })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">프로젝트</h1>
          <p className="text-muted-foreground">진행 중인 프로젝트를 관리하세요</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              프로젝트 생성
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>새 프로젝트 생성</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              {error && (
                <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
                  {error}
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="slug">Slug (고유 식별자)</Label>
                <Input
                  id="slug"
                  value={form.slug}
                  onChange={(e) => setForm({ ...form, slug: e.target.value })}
                  placeholder="my-project"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">이름</Label>
                <Input
                  id="name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="프로젝트 이름"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="repo">Repo URL (선택)</Label>
                <Input
                  id="repo"
                  value={form.repo_url}
                  onChange={(e) => setForm({ ...form, repo_url: e.target.value })}
                  placeholder="https://github.com/..."
                />
              </div>
              <Button type="submit" className="w-full" disabled={createMutation.isPending}>
                {createMutation.isPending ? '생성 중...' : '생성'}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      ) : projects?.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12">
          <FolderKanban className="h-12 w-12 text-muted-foreground" />
          <p className="mt-4 text-lg font-medium">프로젝트가 없습니다</p>
          <p className="text-muted-foreground">새 프로젝트를 생성하여 시작하세요</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Link key={project.id} to={`/projects/${project.slug}`}>
              <Card className="transition-colors hover:bg-accent">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">{project.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{project.slug}</p>
                  {project.repo_url && (
                    <p className="mt-1 text-xs text-muted-foreground truncate">{project.repo_url}</p>
                  )}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
