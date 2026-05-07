import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ArrowLeft, Save, RotateCcw, Check, Clock, AlertCircle, CheckCircle2, Circle, MessageSquare } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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

const stateIcons = {
  todo: Circle,
  in_progress: Clock,
  review: AlertCircle,
  done: CheckCircle2,
}

const stateColors = {
  todo: 'bg-muted text-muted-foreground',
  in_progress: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
  review: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/20',
  done: 'bg-green-500/15 text-green-400 border-green-500/20',
}

export default function IssueDetailPage() {
  const { slug, identifier } = useParams()
  const navigate = useNavigate()
  const { user, authFetch } = useAuth()
  const queryClient = useQueryClient()
  const [isEditing, setIsEditing] = useState(false)

  const { data: issue, isLoading } = useQuery({
    queryKey: ['issue', identifier],
    queryFn: async () => {
      const res = await authFetch(`/api/v1/issues/${identifier}`)
      if (!res.ok) throw new Error('이슈를 찾을 수 없습니다')
      return res.json()
    },
  })

  const { data: projectUsers } = useQuery({
    queryKey: ['project-members', slug],
    queryFn: async () => {
      const res = await authFetch(`/api/v1/projects/${slug}/members`)
      if (!res.ok) return []
      return res.json()
    },
    enabled: !!slug,
  })

  const [editForm, setEditForm] = useState(null)
  const [commentText, setCommentText] = useState('')

  const updateMutation = useMutation({
    mutationFn: async (body) => {
      const res = await authFetch(`/api/v1/issues/${identifier}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error('업데이트 실패')
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['issue', identifier] })
      queryClient.invalidateQueries({ queryKey: ['issues', slug] })
      setIsEditing(false)
      toast.success('이슈가 업데이트되었습니다')
    },
    onError: () => toast.error('업데이트에 실패했습니다'),
  })

  const handleStateChange = (newState) => {
    updateMutation.mutate({ state: newState })
  }

  const commentMutation = useMutation({
    mutationFn: async (content) => {
      const res = await authFetch(`/api/v1/issues/${identifier}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      })
      if (!res.ok) throw new Error('댓글 작성 실패')
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['issue', identifier] })
      setCommentText('')
      toast.success('댓글이 작성되었습니다')
    },
    onError: () => toast.error('댓글 작성에 실패했습니다'),
  })

  const handleCommentSubmit = () => {
    if (commentText.trim()) {
      commentMutation.mutate(commentText.trim())
    }
  }

  const startEditing = () => {
    setEditForm({
      title: issue.title,
      body: issue.body || '',
      priority: issue.priority,
      assignee_id: issue.assignee_id || undefined,
    })
    setIsEditing(true)
  }

  const saveEdit = () => {
    const body = {}
    if (editForm.title !== issue.title) body.title = editForm.title
    if (editForm.body !== (issue.body || '')) body.body = editForm.body
    if (editForm.priority !== issue.priority) body.priority = editForm.priority
    if (editForm.assignee_id !== (issue.assignee_id || '')) {
      body.assignee_id = editForm.assignee_id || null
    }
    if (Object.keys(body).length > 0) {
      updateMutation.mutate(body)
    } else {
      setIsEditing(false)
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!issue) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-lg text-muted-foreground">이슈를 찾을 수 없습니다</p>
        <Button variant="link" onClick={() => navigate(`/projects/${slug}`)}>
          프로젝트로 돌아가기
        </Button>
      </div>
    )
  }

  const StateIcon = stateIcons[issue.state]

  return (
    <div className="space-y-6">
      {/* 상단 네비게이션 */}
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={() => navigate(`/projects/${slug}`)}>
          <ArrowLeft className="mr-1 h-4 w-4" />
          프로젝트로 돌아가기
        </Button>
      </div>

      {/* 헤더 */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="font-mono text-xs">
            {issue.identifier}
          </Badge>
          <Badge className={stateColors[issue.state]}>
            <StateIcon className="mr-1 h-3 w-3" />
            {stateLabels[issue.state]}
          </Badge>
          <Badge variant="outline">P{issue.priority}</Badge>
        </div>

        {isEditing ? (
          <div className="space-y-3">
            <Input
              value={editForm.title}
              onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
              className="text-xl font-bold"
            />
            <div className="flex gap-2">
              <Button onClick={saveEdit} disabled={updateMutation.isPending}>
                <Save className="mr-2 h-4 w-4" />
                저장
              </Button>
              <Button variant="ghost" onClick={() => setIsEditing(false)}>
                취소
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between gap-4">
            <h1 className="text-2xl font-bold tracking-tight">{issue.title}</h1>
            <Button variant="outline" size="sm" onClick={startEditing}>
              편집
            </Button>
          </div>
        )}
      </div>

      <Separator />

      <div className="grid gap-6 lg:grid-cols-4">
        {/* 메인 콘텐츠 */}
        <div className="lg:col-span-3 space-y-6">
          {/* 본문 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">내용</CardTitle>
            </CardHeader>
            <CardContent>
              {isEditing ? (
                <Textarea
                  value={editForm.body}
                  onChange={(e) => setEditForm({ ...editForm, body: e.target.value })}
                  rows={12}
                  placeholder="Markdown 지원"
                />
              ) : (
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{issue.body || '내용이 없습니다'}</ReactMarkdown>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 댓글 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                댓글 {issue.comments?.length || 0}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                {issue.comments?.length === 0 ? (
                  <p className="text-sm text-muted-foreground">댓글이 없습니다</p>
                ) : (
                  issue.comments?.map((comment) => (
                    <div key={comment.id} className="rounded-md border p-3 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{comment.author_name}</span>
                        <span className="text-xs text-muted-foreground">
                          {new Date(comment.created_at).toLocaleDateString('ko-KR')}
                        </span>
                      </div>
                      <p className="text-sm whitespace-pre-wrap">{comment.content}</p>
                    </div>
                  ))
                )}
              </div>
              <div className="space-y-2">
                <Textarea
                  placeholder="댓글을 입력하세요..."
                  rows={3}
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                />
                <Button
                  size="sm"
                  onClick={handleCommentSubmit}
                  disabled={!commentText.trim() || commentMutation.isPending}
                >
                  {commentMutation.isPending ? '작성 중...' : '댓글 작성'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* 상태 변경 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">상태 변경</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {Object.entries(stateLabels).map(([key, label]) => {
                const Icon = stateIcons[key]
                const active = issue.state === key
                return (
                  <Button
                    key={key}
                    variant={active ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleStateChange(key)}
                    disabled={updateMutation.isPending}
                  >
                    <Icon className="mr-1 h-4 w-4" />
                    {label}
                  </Button>
                )
              })}
            </CardContent>
          </Card>
        </div>

        {/* 사이드 정보 */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">속성</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* 프로젝트 */}
              <div>
                <Label className="text-xs text-muted-foreground">프로젝트</Label>
                <p className="text-sm font-medium">
                  <Link to={`/projects/${slug}`} className="hover:underline">
                    {issue.project?.name || slug}
                  </Link>
                </p>
              </div>

              {/* 보고자 */}
              <div>
                <Label className="text-xs text-muted-foreground">보고자</Label>
                <p className="text-sm font-medium">{issue.reporter?.name || '-'}</p>
              </div>

              {/* 생성자 */}
              <div>
                <Label className="text-xs text-muted-foreground">생성자</Label>
                <p className="text-sm font-medium">
                  {issue.created_by_agent_id
                    ? `${issue.created_by_user?.name || '-'}(agent)`
                    : issue.created_by_user?.name || '-'}
                </p>
              </div>

              <Separator />

              {/* 담당자 */}
              <div>
                <Label className="text-xs text-muted-foreground">담당자</Label>
                {isEditing ? (
                  <Select
                    value={editForm.assignee_id || 'unassigned'}
                    onValueChange={(v) => setEditForm({ ...editForm, assignee_id: v === 'unassigned' ? '' : v })}
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue placeholder="담당자 선택" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="unassigned">미지정</SelectItem>
                      {projectUsers?.filter((m) => m.user_id).map((m) => (
                        <SelectItem key={m.user_id} value={String(m.user_id)}>
                          {m.user?.name || m.user_id}
                        </SelectItem>
                      ))}
                      {(!projectUsers || projectUsers.filter((m) => m.user_id).length === 0) && (
                        <div className="px-2 py-1.5 text-xs text-muted-foreground">
                          프로젝트에 등록된 멤버가 없습니다.
                        </div>
                      )}
                    </SelectContent>
                  </Select>
                ) : (
                  <p className="text-sm font-medium">{issue.assignee?.name || '미지정'}</p>
                )}
              </div>

              {/* 우선순위 */}
              <div>
                <Label className="text-xs text-muted-foreground">우선순위</Label>
                {isEditing ? (
                  <Select
                    value={String(editForm.priority)}
                    onValueChange={(v) => setEditForm({ ...editForm, priority: parseInt(v) })}
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1 - 긴급</SelectItem>
                      <SelectItem value="2">2 - 높음</SelectItem>
                      <SelectItem value="3">3 - 보통</SelectItem>
                      <SelectItem value="4">4 - 낮음</SelectItem>
                    </SelectContent>
                  </Select>
                ) : (
                  <p className="text-sm font-medium">{issue.priority}</p>
                )}
              </div>

              <Separator />

              {/* 날짜 */}
              <div>
                <Label className="text-xs text-muted-foreground">생성일</Label>
                <p className="text-sm">
                  {issue.created_at
                    ? new Date(issue.created_at).toLocaleDateString('ko-KR')
                    : '-'}
                </p>
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">수정일</Label>
                <p className="text-sm">
                  {issue.updated_at
                    ? new Date(issue.updated_at).toLocaleDateString('ko-KR')
                    : '-'}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* review 상태일 때 승인/거절 */}
          {issue.state === 'review' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">검토 액션</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => handleStateChange('in_progress')}
                  disabled={updateMutation.isPending}
                >
                  <RotateCcw className="mr-2 h-4 w-4" />
                  재작업 요청
                </Button>
                <Button
                  className="w-full"
                  onClick={() => handleStateChange('done')}
                  disabled={updateMutation.isPending}
                >
                  <Check className="mr-2 h-4 w-4" />
                  승인 (완료)
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
