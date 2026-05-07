import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'

function AgentSettings() {
  const { authFetch } = useAuth()
  const [keys, setKeys] = useState([])
  const [newKeyName, setNewKeyName] = useState('')
  const [newKey, setNewKey] = useState(null)
  const [loading, setLoading] = useState(false)
  const [selectedKeyId, setSelectedKeyId] = useState(null)
  const [copied, setCopied] = useState(null)

  const apiBaseUrl = `${window.location.origin}/api/v1`

  const fetchKeys = async () => {
    const res = await authFetch('/api/v1/auth/api-keys')
    if (res.ok) {
      const data = await res.json()
      setKeys(data)
      if (data.length > 0 && !selectedKeyId) {
        setSelectedKeyId(data[0].id)
      }
    }
  }

  useEffect(() => {
    fetchKeys()
  }, [])

  useEffect(() => {
    if (newKey) {
      setSelectedKeyId(newKey.id)
    }
  }, [newKey])

  const handleCreate = async () => {
    if (!newKeyName.trim()) return
    setLoading(true)
    try {
      const res = await authFetch('/api/v1/auth/api-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newKeyName })
      })
      if (res.ok) {
        const data = await res.json()
        setNewKey(data)
        setNewKeyName('')
        fetchKeys()
      }
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (keyId) => {
    if (!confirm('정말 삭제하시겠습니까?')) return
    const res = await authFetch(`/api/v1/auth/api-keys/${keyId}`, {
      method: 'DELETE'
    })
    if (res.ok) {
      if (selectedKeyId === keyId) {
        setSelectedKeyId(null)
      }
      fetchKeys()
    }
  }

  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text)
    setCopied(label)
    setTimeout(() => setCopied(null), 2000)
  }

  const selectedKey = keys.find(k => k.id === selectedKeyId)
  const displayKey = newKey?.key || selectedKey?.key || 'YOUR_API_KEY_HERE'
  const projectPath = '/path/to/symphony-lite'
  const venvPython = '<venv>/bin/python'

  const mcpJson = JSON.stringify({
    mcpServers: {
      'symphony-lite': {
        command: venvPython,
        args: [`${projectPath}/mcp/server.py`],
        env: {
          SYMPHONY_API_URL: apiBaseUrl,
          SYMPHONY_API_KEY: displayKey === 'YOUR_API_KEY_HERE' ? displayKey : displayKey
        }
      }
    }
  }, null, 2)

  const kimiCommand = `kimi mcp add --transport stdio symphony-lite \\\n  --env SYMPHONY_API_URL=${apiBaseUrl} \\\n  --env SYMPHONY_API_KEY=${displayKey} \\\n  -- ${venvPython} ${projectPath}/mcp/server.py`

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <h1>🤖 에이전트 설정</h1>
      <p>AI 에이전트(Kimi, Claude 등)가 Symphony Lite에 연결할 수 있는 API 키를 관리합니다.</p>

      {newKey && (
        <div style={{ padding: '1rem', marginBottom: '1rem', background: '#d4edda', borderRadius: '4px', border: '1px solid #c3e6cb' }}>
          <h3>✅ 새 API 키가 발행되었습니다</h3>
          <p style={{ color: '#721c24', fontWeight: 'bold' }}>이 키는 지금만 표시됩니다. 반드시 저장하세요!</p>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <code style={{ padding: '0.5rem', background: '#f8f9fa', borderRadius: '4px', flex: 1, wordBreak: 'break-all' }}>
              {newKey.key}
            </code>
            <button onClick={() => copyToClipboard(newKey.key, 'newKey')} style={{ padding: '0.5rem 1rem' }}>
              {copied === 'newKey' ? '✅ 복사됨' : '복사'}
            </button>
          </div>
          <button onClick={() => setNewKey(null)} style={{ marginTop: '0.5rem' }}>닫기</button>
        </div>
      )}

      <div style={{ marginBottom: '2rem', padding: '1rem', background: '#f8f9fa', borderRadius: '4px' }}>
        <h3>새 API 키 발행</h3>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            type="text"
            placeholder="에이전트 이름 (예: 내 노트북 Kimi)"
            value={newKeyName}
            onChange={e => setNewKeyName(e.target.value)}
            style={{ flex: 1, padding: '0.5rem' }}
          />
          <button
            onClick={handleCreate}
            disabled={loading}
            style={{ padding: '0.5rem 1rem', background: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            {loading ? '발행 중...' : '발행'}
          </button>
        </div>
      </div>

      <h3>발행된 API 키 목록</h3>
      {keys.length === 0 ? (
        <p>발행된 API 키가 없습니다. 위에서 키를 발행하면 MCP 설정 예시에 자동 반영됩니다.</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #dee2e6' }}>
              <th style={{ textAlign: 'left', padding: '0.75rem', width: '40px' }}></th>
              <th style={{ textAlign: 'left', padding: '0.75rem' }}>이름</th>
              <th style={{ textAlign: 'left', padding: '0.75rem' }}>발행일</th>
              <th style={{ textAlign: 'left', padding: '0.75rem' }}>마지막 사용</th>
              <th style={{ textAlign: 'right', padding: '0.75rem' }}>관리</th>
            </tr>
          </thead>
          <tbody>
            {keys.map(key => (
              <tr key={key.id} style={{ borderBottom: '1px solid #dee2e6', background: selectedKeyId === key.id ? '#e7f3ff' : 'transparent' }}>
                <td style={{ padding: '0.75rem' }}>
                  <input
                    type="radio"
                    name="selectedKey"
                    checked={selectedKeyId === key.id}
                    onChange={() => setSelectedKeyId(key.id)}
                  />
                </td>
                <td style={{ padding: '0.75rem' }}>{key.name}</td>
                <td style={{ padding: '0.75rem' }}>{new Date(key.created_at).toLocaleDateString()}</td>
                <td style={{ padding: '0.75rem' }}>{key.last_used_at ? new Date(key.last_used_at).toLocaleString() : '-'}</td>
                <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                  <button
                    onClick={() => handleDelete(key.id)}
                    style={{ background: '#dc3545', color: 'white', border: 'none', padding: '0.25rem 0.5rem', borderRadius: '4px', cursor: 'pointer' }}
                  >
                    삭제
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={{ marginTop: '2rem', padding: '1rem', background: '#e2e3e5', borderRadius: '4px' }}>
        <h4>🔌 MCP 연동 설정</h4>
        <p style={{ marginBottom: '1rem' }}>
          아래 설정은 <strong>현재 접속한 서버({apiBaseUrl})</strong>와 <strong>선택한 API 키</strong>를 반영합니다.
          <br />
          <code style={{ color: '#856404', background: '#fff3cd', padding: '0.1rem 0.3rem', borderRadius: '3px' }}>{venvPython}</code>와 <code style={{ color: '#856404', background: '#fff3cd', padding: '0.1rem 0.3rem', borderRadius: '3px' }}>{projectPath}</code>는 본인 환경에 맞게 수정하세요.
        </p>

        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <h5 style={{ margin: 0 }}>방법 1: mcp.json 파일</h5>
            <button
              onClick={() => copyToClipboard(mcpJson, 'mcpJson')}
              style={{ padding: '0.25rem 0.75rem', fontSize: '0.875rem' }}
            >
              {copied === 'mcpJson' ? '✅ 복사됨' : '복사'}
            </button>
          </div>
          <pre style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '4px', overflow: 'auto', fontSize: '0.875rem' }}>
            {mcpJson}
          </pre>
          <p style={{ fontSize: '0.8rem', color: '#6c757d' }}>
            파일 위치: <code>~/.kimi/mcp.json</code> (macOS/Linux) → 이후 <code>kimi</code> 실행 시 자동 로드
          </p>
        </div>

        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <h5 style={{ margin: 0 }}>방법 2: CLI로 등록</h5>
            <button
              onClick={() => copyToClipboard(kimiCommand, 'kimiCommand')}
              style={{ padding: '0.25rem 0.75rem', fontSize: '0.875rem' }}
            >
              {copied === 'kimiCommand' ? '✅ 복사됨' : '복사'}
            </button>
          </div>
          <pre style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '4px', overflow: 'auto', fontSize: '0.875rem' }}>
            {kimiCommand}
          </pre>
          <p style={{ fontSize: '0.8rem', color: '#6c757d' }}>
            등록 후 <code>kimi mcp list</code>로 확인
          </p>
        </div>
      </div>
    </div>
  )
}

export default AgentSettings
