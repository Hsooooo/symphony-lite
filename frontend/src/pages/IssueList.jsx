import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

function IssueList() {
  const { authFetch } = useAuth()
  const [projects, setProjects] = useState([])
  const [selectedProject, setSelectedProject] = useState('')
  const [issues, setIssues] = useState([])
  const [loading, setLoading] = useState(true)

  // 프로젝트 목록 조회
  useEffect(() => {
    authFetch('/api/v1/teams')
      .then(r => r.json())
      .then(teams => {
        if (teams.length > 0) {
          return authFetch(`/api/v1/projects/team/${teams[0].slug}`)
        }
        return { json: () => [] }
      })
      .then(r => r.json())
      .then(data => {
        setProjects(data)
        if (data.length > 0) {
          setSelectedProject(data[0].slug)
        }
      })
  }, [])

  // 선택된 프로젝트의 이슈 조회
  useEffect(() => {
    if (!selectedProject) return
    setLoading(true)
    authFetch(`/api/v1/issues/project/${selectedProject}`)
      .then(r => r.json())
      .then(data => {
        setIssues(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [selectedProject])

  const [showForm, setShowForm] = useState(false)
  const [newIssue, setNewIssue] = useState({ title: '', body: '', priority: 3 })
  const [creating, setCreating] = useState(false)

  const handleCreateIssue = async () => {
    if (!newIssue.title.trim()) return
    setCreating(true)
    try {
      const res = await authFetch(`/api/v1/issues/project/${selectedProject}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newIssue,
          identifier: `${selectedProject.toUpperCase()}-${Date.now()}`,
          project_id: projects.find(p => p.slug === selectedProject)?.id,
          team_id: projects.find(p => p.slug === selectedProject)?.team_id
        })
      })
      if (res.ok) {
        setNewIssue({ title: '', body: '', priority: 3 })
        setShowForm(false)
        // 목록 새로고침
        const issuesRes = await authFetch(`/api/v1/issues/project/${selectedProject}`)
        const data = await issuesRes.json()
        setIssues(data)
      }
    } finally {
      setCreating(false)
    }
  }

  if (loading && issues.length === 0) return <p>로딩 중...</p>

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h1>이슈 목록</h1>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <select 
            value={selectedProject} 
            onChange={e => setSelectedProject(e.target.value)}
            style={{ padding: '0.5rem', fontSize: '1rem' }}
          >
            {projects.map(p => (
              <option key={p.id} value={p.slug}>{p.name}</option>
            ))}
          </select>
          <button
            onClick={() => setShowForm(!showForm)}
            style={{ padding: '0.5rem 1rem', background: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            + 이슈 생성
          </button>
        </div>
      </div>

      {showForm && (
        <div style={{ marginBottom: '1rem', padding: '1rem', background: '#f8f9fa', borderRadius: '4px' }}>
          <h3>새 이슈 생성</h3>
          <div style={{ marginBottom: '0.5rem' }}>
            <input
              type="text"
              placeholder="제목"
              value={newIssue.title}
              onChange={e => setNewIssue({ ...newIssue, title: e.target.value })}
              style={{ width: '100%', padding: '0.5rem', marginBottom: '0.5rem' }}
            />
            <textarea
              placeholder="본문 (Markdown)"
              value={newIssue.body}
              onChange={e => setNewIssue({ ...newIssue, body: e.target.value })}
              rows={4}
              style={{ width: '100%', padding: '0.5rem', marginBottom: '0.5rem' }}
            />
            <select
              value={newIssue.priority}
              onChange={e => setNewIssue({ ...newIssue, priority: parseInt(e.target.value) })}
              style={{ padding: '0.5rem' }}
            >
              <option value={1}>1 - 긴급</option>
              <option value={2}>2 - 높음</option>
              <option value={3}>3 - 보통</option>
              <option value={4}>4 - 낮음</option>
            </select>
          </div>
          <div>
            <button
              onClick={handleCreateIssue}
              disabled={creating}
              style={{ marginRight: '0.5rem', padding: '0.5rem 1rem', background: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
            >
              {creating ? '생성 중...' : '생성'}
            </button>
            <button
              onClick={() => setShowForm(false)}
              style={{ padding: '0.5rem 1rem', background: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
            >
              취소
            </button>
          </div>
        </div>
      )}

      {issues.length === 0 ? (
        <p>등록된 이슈가 없습니다.</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {issues.map(issue => (
            <li key={issue.id} style={{ 
              marginBottom: '1rem', 
              padding: '1rem', 
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Link to={`/issues/${issue.identifier}`} style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>
                  {issue.identifier}: {issue.title}
                </Link>
                <span style={{ 
                  padding: '0.25rem 0.5rem', 
                  borderRadius: '4px',
                  background: issue.state === 'done' ? '#d4edda' : 
                              issue.state === 'in_progress' ? '#fff3cd' : 
                              issue.state === 'review' ? '#cce5ff' : '#e2e3e5'
                }}>
                  {issue.state}
                </span>
              </div>
              <div style={{ marginTop: '0.5rem', color: '#666', fontSize: '0.9rem' }}>
                우선순위: {issue.priority} | 라벨: {issue.labels?.join(', ') || '-'} | 생성일: {new Date(issue.created_at).toLocaleDateString()}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default IssueList
