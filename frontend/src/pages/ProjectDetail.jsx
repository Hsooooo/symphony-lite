import { useState, useMemo } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, Filter, ArrowUpDown,
  Ticket, GitBranch, Calendar
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { toast } from 'sonner'

const stateLabels = {
  todo: '할 일',
  in_progress: '진행 중',
  review: '검토',
  done: '완료',
}

const stateColors = {
  todo: 'bg-muted text-muted-foreground',
  in_progress: 'bg-blue-500/15 text-blue-400',
  review: 'bg-yellow-500/15 text-yellow-400',
  done: 'bg-green-500/15 text-green-400',
}

export default function ProjectDetail() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { authFetch } = useAuth()
  const queryClient = useQueryClient()

  const [filterState, setFilterState] = useState('all')
  const [sortBy, setSortBy] = useState('newest')
  const [createOpen, setCreateOpen] = useState(false)
  const [newIssue, setNewIssue] = useState({ title: '', body: '', priority: 3 })

  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['project', slug],
    queryFn: async () => {
      const res = await authFetch(`/api/v1/projects/${slug}`)
      if (!res.ok) throw new Error('프로젝트를 찾을 수 없습니다')
      return res.json()
    },
  })

  const { data: issues, isLoading: issuesLoading } = useQuery({
    queryKey: ['issues', slug],
    queryFn: async () => {
      const res = await authFetch(`/api/v1/issues/project/${slug}`)
      if (!res.ok) return []
      return res.json()
    },
  })

  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await authFetch(`/api/v1/issues/project/${slug}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newIssue,
          identifier: `${slug.toUpperCase()}-${Date.now().toString(36).toUpperCase()}`,
          project_id: project?.id,
          team_id: project?.team_id,
        }),
      })
      if (!res.ok) throw new Error('생성 실패')
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['issues', slug] })
      setNewIssue({ title: '', body: '', priority: 3 })
      setCreateOpen(false)
      toast.success('이슈가 생성되었습니다')
    },
    onError: () => toast.error('이슈 생성에 실패했습니다'),
  })

  const filteredIssues = useMemo(() => {
    let list = issues || []
    if (filterState !== 'all') {
      list = list.filter((i) => i.state === filterState)
    }
    if (sortBy === 'newest') {
      list = [...list].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    } else if (sortBy === 'priority') {
      list = [...list].sort((a, b) => a.priority - b.priority)
    } else if (sortBy === 'state') {
      const order = { todo: 0, in_progress: 1, review: 2, done: 3 }
      list = [...list].sort((a, b) => order[a.state] - order[b.state])
    }
    return list
  }, [issues, filterState, sortBy])

  return (
    <div className="space-y-6">
      {projectLoading ? (
        <Skeleton className="h-20 w-full" />
      ) : (
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight">{project?.name}</h1>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <GitBranch className="h-3.5 w-3.5" />
              {project?.slug}
            </span>
            {project?.repo_url && (
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                {project.repo_url}
              </span>
            )}
          </div>
        </div>
      )}

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <Select value={filterState} onValueChange={setFilterState}>
            <SelectTrigger className="w-[140px]">
              <Filter className="mr-2 h-4 w-4" />
              <SelectValue placeholder="상태" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">전체</SelectItem>
              <SelectItem value="todo">할 일</SelectItem>
              <SelectItem value="in_progress">진행 중</SelectItem>
              <SelectItem value="review">검토</SelectItem>
              <SelectItem value="done">완료</SelectItem>
            </SelectContent>
          </Select>

          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-[140px]">
              <ArrowUpDown className="mr-2 h-4 w-4" />
              <SelectValue placeholder="정렬" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">최신순</SelectItem>
              <SelectItem value="priority">우선순위</SelectItem>
              <SelectItem value="state">상태순</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          이슈 생성
        </Button>
      </div>

      {issuesLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : filteredIssues.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12">
          <Ticket className="h-12 w-12 text-muted-foreground" />
          <p className="mt-4 text-lg font-medium">이슈가 없습니다</p>
          <p className="text-muted-foreground">새 이슈를 생성하여 시작하세요</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredIssues.map((issue) => (
            <Link
              key={issue.id}
              to={`/projects/${slug}/issues/${issue.identifier}`}
              className="flex items-center justify-between rounded-lg border bg-card p-4 transition-colors hover:bg-accent"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
                  <Ticket className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="min-w-0">
                  <p className="truncate font-medium">{issue.title}</p>
                  <p className="text-xs text-muted-foreground">{issue.identifier}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0 ml-4">
                <Badge className={stateColors[issue.state]}>{stateLabels[issue.state]}</Badge>
                <span className="text-xs text-muted-foreground hidden sm:inline">P{issue.priority}</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* 이슈 생성 사이드 패널 */}
      <Sheet open={createOpen} onOpenChange={setCreateOpen}>
        <SheetContent className="w-full sm:max-w-lg">
          <SheetHeader>
            <SheetTitle>새 이슈 생성</SheetTitle>
          </SheetHeader>
          <div className="mt-6 space-y-4">
            <div className="space-y-2">
              <Label>제목</Label>
              <Input
                placeholder="이슈 제목"
                value={newIssue.title}
                onChange={(e) => setNewIssue({ ...newIssue, title: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>본문 (Markdown)</Label>
              <textarea
                placeholder="이슈 내용을 입력하세요"
                value={newIssue.body}
                onChange={(e) => setNewIssue({ ...newIssue, body: e.target.value })}
                rows={8}
                className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>
            <div className="space-y-2">
              <Label>우선순위</Label>
              <Select
                value={String(newIssue.priority)}
                onValueChange={(v) => setNewIssue({ ...newIssue, priority: parseInt(v) })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 - 긴급</SelectItem>
                  <SelectItem value="2">2 - 높음</SelectItem>
                  <SelectItem value="3">3 - 보통</SelectItem>
                  <SelectItem value="4">4 - 낮음</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-2 pt-4">
              <Button
                className="flex-1"
                onClick={() => createMutation.mutate()}
                disabled={!newIssue.title.trim() || createMutation.isPending}
              >
                {createMutation.isPending ? '생성 중...' : '생성'}
              </Button>
              <Button variant="ghost" onClick={() => setCreateOpen(false)}>
                취소
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  )
}
