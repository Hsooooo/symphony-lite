import { useAuth } from '@/contexts/AuthContext'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function Settings() {
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">설정</h1>
        <p className="text-muted-foreground">계정 정보를 확인하세요</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>내 정보</CardTitle>
          <CardDescription>현재 로그인된 계정 정보입니다</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">이름</p>
              <p className="font-medium">{user?.name}</p>
            </div>
            <div>
              <p className="text-muted-foreground">아이디</p>
              <p className="font-medium">{user?.username}</p>
            </div>
            <div>
              <p className="text-muted-foreground">소속 팀</p>
              <Badge variant="secondary">{user?.team?.name || '-'}</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
