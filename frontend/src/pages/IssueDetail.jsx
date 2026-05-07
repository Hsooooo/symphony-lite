import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { useAuth } from '../contexts/AuthContext'

function IssueDetail() {
  const { identifier } = useParams()
  const navigate = useNavigate()
  const { authFetch } = useAuth()
  const [issue, setIssue] = useState(null)
  const [workLogs, setWorkLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [activeProposalId, setActiveProposalId] = useState(null)

  const fetchIssue = () => {
    setLoading(true)
    Promise.all([
      authFetch(`/api/v1/issues/${identifier}`),
      authFetch(`/api/v1/issues/${identifier}/work-logs`)
    ])
      .then(([issueRes, logsRes]) => Promise.all([issueRes.json(), logsRes.json()]))
      .then(([issueData, logsData]) => {
        setIssue(issueData)
        setWorkLogs(logsData)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  useEffect(() => {
    fetchIssue()
  }, [identifier])

  const handleApprove = async (proposalId) => {
    setActionLoading(true)
    try {
      const res = await authFetch(`/api/v1/status-proposals/${proposalId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved_by: '00000000-0000-0000-0000-000000000001' })
      })
      if (res.ok) {
        alert('승인 완료')
        fetchIssue()
      } else {
        alert('승인 실패')
      }
    } finally {
      setActionLoading(false)
    }
  }

  const handleReject = async (proposalId) => {
    if (!rejectReason.trim()) {
      alert('거절 사유를 입력하세요')
      return
    }
    setActionLoading(true)
    try {
      const res = await authFetch(`/api/v1/status-proposals/${proposalId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rejected_by: '00000000-0000-0000-0000-000000000001',
          rejected_reason: rejectReason
        })
      })
      if (res.ok) {
        alert('거절 완료')
        setRejectReason('')
        setActiveProposalId(null)
        fetchIssue()
      } else {
        alert('거절 실패')
      }
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) return <p>로딩 중...</p>
  if (!issue) return <p>이슈를 찾을 수 없습니다.</p>

  const pendingProposals = issue.status_proposals?.filter(p => p.status === 'pending') || []
  const historyProposals = issue.status_proposals?.filter(p => p.status !== 'pending') || []

  return (
    <div>
      <button onClick={() => navigate('/issues')} style={{ marginBottom: '1rem' }}>
        ← 이슈 목록
      </button>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h1>{issue.identifier}: {issue.title}</h1>
        <span style={{ 
          padding: '0.5rem 1rem', 
          borderRadius: '4px',
          background: issue.state === 'done' ? '#d4edda' : 
                      issue.state === 'in_progress' ? '#fff3cd' : 
                      issue.state === 'review' ? '#cce5ff' : '#e2e3e5',
          fontWeight: 'bold'
        }}>
          {issue.state}
        </span>
      </div>

      {/* 본문 */}
      <div style={{ marginBottom: '2rem' }}>
        <h2>본문</h2>
        <div style={{ padding: '1rem', background: '#f8f9fa', borderRadius: '4px' }}>
          {issue.body ? <ReactMarkdown>{issue.body}</ReactMarkdown> : <p>본문이 없습니다.</p>}
        </div>
      </div>

      {/* Workpad */}
      {issue.workpad && (
        <div style={{ marginBottom: '2rem' }}>
          <h2>🤖 Workpad (에이전트 진행 상황)</h2>
          <div style={{ padding: '1rem', background: '#f0f8ff', borderRadius: '4px', border: '1px solid #bee5eb' }}>
            <ReactMarkdown>{issue.workpad}</ReactMarkdown>
          </div>
          <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.5rem' }}>
            마지막 업데이트: {issue.workpad_updated_at ? new Date(issue.workpad_updated_at).toLocaleString() : '-'}
          </div>
        </div>
      )}

      {/* 승인 대기 중인 제안 */}
      {pendingProposals.length > 0 && (
        <div style={{ marginBottom: '2rem', padding: '1rem', background: '#fff3cd', borderRadius: '4px', border: '1px solid #ffc107' }}>
          <h2>⏳ 승인 대기 중인 상태 변경</h2>
          {pendingProposals.map(p => (
            <div key={p.id} style={{ marginBottom: '1rem', padding: '1rem', background: 'white', borderRadius: '4px' }}>
              <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>
                {p.from_state} → {p.to_state}
              </div>
              <div style={{ color: '#666', marginBottom: '0.5rem' }}>
                사유: {p.reason || '(사유 없음)'}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#888', marginBottom: '1rem' }}>
                제안: {p.proposed_by} | {new Date(p.created_at).toLocaleString()}
              </div>
              
              {activeProposalId === p.id ? (
                <div style={{ marginTop: '0.5rem' }}>
                  <textarea
                    placeholder="거절 사유를 입력하세요"
                    value={rejectReason}
                    onChange={e => setRejectReason(e.target.value)}
                    style={{ width: '100%', padding: '0.5rem', marginBottom: '0.5rem' }}
                    rows={2}
                  />
                  <div>
                    <button 
                      onClick={() => handleReject(p.id)}
                      disabled={actionLoading}
                      style={{ marginRight: '0.5rem', background: '#dc3545', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' }}
                    >
                      거절 확인
                    </button>
                    <button 
                      onClick={() => { setActiveProposalId(null); setRejectReason(''); }}
                      style={{ background: '#6c757d', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' }}
                    >
                      취소
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <button 
                    onClick={() => handleApprove(p.id)}
                    disabled={actionLoading}
                    style={{ marginRight: '0.5rem', background: '#28a745', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' }}
                  >
                    ✅ 승인
                  </button>
                  <button 
                    onClick={() => setActiveProposalId(p.id)}
                    disabled={actionLoading}
                    style={{ background: '#dc3545', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' }}
                  >
                    ❌ 거절
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 상태 변경 이력 */}
      {historyProposals.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <h2>📋 상태 변경 이력</h2>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {historyProposals.map(p => (
              <li key={p.id} style={{ 
                padding: '0.75rem', 
                marginBottom: '0.5rem',
                background: p.status === 'approved' ? '#d4edda' : '#f8d7da',
                borderRadius: '4px'
              }}>
                <strong>{p.from_state} → {p.to_state}</strong>
                {' '}({p.status === 'approved' ? '승인' : '거절'})
                <div style={{ fontSize: '0.85rem', color: '#666' }}>
                  사유: {p.reason || '-'} | {new Date(p.created_at).toLocaleString()}
                  {p.rejected_reason && ` | 거절 사유: ${p.rejected_reason}`}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 작업 로그 타임라인 */}
      {workLogs.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <h2>📊 작업 로그</h2>
          <div style={{ borderLeft: '2px solid #dee2e6', paddingLeft: '1rem' }}>
            {workLogs.map(log => (
              <div key={log.id} style={{ marginBottom: '1rem', position: 'relative' }}>
                <div style={{ 
                  position: 'absolute', 
                  left: '-1.35rem', 
                  top: '0.3rem',
                  width: '10px', 
                  height: '10px', 
                  borderRadius: '50%', 
                  background: '#007bff' 
                }} />
                <div style={{ fontSize: '0.8rem', color: '#888' }}>
                  {new Date(log.created_at).toLocaleString()}
                  {log.agent_id && ` | 에이전트: ${log.agent_id}`}
                </div>
                <div style={{ fontWeight: 'bold' }}>
                  {log.event_type}
                </div>
                {log.payload && Object.keys(log.payload).length > 0 && (
                  <pre style={{ fontSize: '0.8rem', background: '#f8f9fa', padding: '0.5rem', borderRadius: '4px' }}>
                    {JSON.stringify(log.payload, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 메타 정보 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', padding: '1rem', background: '#f8f9fa', borderRadius: '4px' }}>
        <div>
          <h3>메타 정보</h3>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            <li>프로젝트: {issue.project?.name || '-'}</li>
            <li>팀: {issue.team?.name || '-'}</li>
            <li>우선순위: {issue.priority}</li>
            <li>라벨: {issue.labels?.join(', ') || '-'}</li>
            <li>브랜치: {issue.branch_name || '-'}</li>
            <li>PR: {issue.pr_url ? <a href={issue.pr_url} target="_blank" rel="noreferrer">링크</a> : '-'}</li>
          </ul>
        </div>
        <div>
          <h3>시간 정보</h3>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            <li>생성: {new Date(issue.created_at).toLocaleString()}</li>
            <li>수정: {new Date(issue.updated_at).toLocaleString()}</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default IssueDetail
