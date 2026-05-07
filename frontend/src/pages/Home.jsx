import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Ticket, Clock, CheckCircle, AlertCircle } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

export default function Home() {
  const { user, authFetch } = useAuth()

  const { data: myIssues, isLoading } = useQuery({
    queryKey: ['my-issues', user?.id],
    queryFn: async () => {
      const teamsRes = await authFetch('/api/v1/teams')
      const teams = teamsRes.ok ? await teamsRes.json() : []
      if (teams.length === 0) return []
      const projectsRes = await authFetch(`/api/v1/projects/team/${teams[0].slug}`)
      const projects = projectsRes.ok ? await projectsRes.json() : []
      if (projects.length === 0) return []

      const allIssues = []
      for (const p of projects) {
        const res = await authFetch(`/api/v1/issues/project/${p.slug}`)
        if (res.ok) {
          const issues = await res.json()
          allIssues.push(...issues)
        }
      }
      return allIssues
    },
    enabled: !!user,
  })

  const myAssignedIssues = myIssues?.filter((i) => i.assignee_id === user?.id) || []
  const inProgress = myAssignedIssues.filter((i) => i.state === 'in_progress')
  const inReview = myAssignedIssues.filter((i) => i.state === 'review')
  const todo = myAssignedIssues.filter((i) => i.state === 'todo')

  const statCards = [
    { title: '진행 중', count: inProgress.length, icon: Clock, variant: 'default' },
    { title: '검토 대기', count: inReview.length, icon: AlertCircle, variant: 'secondary' },
    { title: '할 일', count: todo.length, icon: Ticket, variant: 'outline' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">대시보드</h1>
        <p className="text-muted-foreground">
          {user?.name}님, 오늘의 작업을 확인하세요
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <Skeleton className="h-7 w-12" />
                ) : (
                  <div className="text-2xl font-bold">{stat.count}</div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">내 진행 중 이슈</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {isLoading ? (
              <Skeleton className="h-16 w-full" />
            ) : inProgress.length === 0 ? (
              <p className="text-sm text-muted-foreground">진행 중인 이슈가 없습니다</p>
            ) : (
              inProgress.slice(0, 5).map((issue) => (
                <Link
                  key={issue.id}
                  to={`/projects/${issue.project?.slug}/issues/${issue.identifier}`}
                  className="flex items-center justify-between rounded-md border p-3 transition-colors hover:bg-accent"
                >
                  <div className="space-y-1">
                    <p className="text-sm font-medium">{issue.title}</p>
                    <p className="text-xs text-muted-foreground">{issue.identifier}</p>
                  </div>
                  <Badge variant="default">진행 중</Badge>
                </Link>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">검토 대기</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {isLoading ? (
              <Skeleton className="h-16 w-full" />
            ) : inReview.length === 0 ? (
              <p className="text-sm text-muted-foreground">검토 대기 중인 이슈가 없습니다</p>
            ) : (
              inReview.slice(0, 5).map((issue) => (
                <Link
                  key={issue.id}
                  to={`/projects/${issue.project?.slug}/issues/${issue.identifier}`}
                  className="flex items-center justify-between rounded-md border p-3 transition-colors hover:bg-accent"
                >
                  <div className="space-y-1">
                    <p className="text-sm font-medium">{issue.title}</p>
                    <p className="text-xs text-muted-foreground">{issue.identifier}</p>
                  </div>
                  <Badge variant="secondary">검토</Badge>
                </Link>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
