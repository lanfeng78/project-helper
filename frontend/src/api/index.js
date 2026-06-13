import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const BASE = '/api'

export async function authedFetch(url, options = {}) {
  const auth = useAuthStore()
  const headers = { ...(options.headers || {}) }

  if (auth.accessToken) {
    headers['Authorization'] = `Bearer ${auth.accessToken}`
  }

  let res = await fetch(url, { ...options, headers })

  if (res.status === 401 && auth.refreshToken) {
    const ok = await auth.tryRefresh()
    if (ok) {
      headers['Authorization'] = `Bearer ${auth.accessToken}`
      res = await fetch(url, { ...options, headers })
    } else {
      router.push('/login')
      throw new Error('会话已过期，请重新登录')
    }
  }

  return res
}

export async function analyzeRepo(repoUrl, mode = 'detail') {
  const res = await authedFetch(`${BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl, mode })
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export function subscribeProgress(projectId, onProgress, onDone, onError) {
  const auth = useAuthStore()
  const url = `${BASE}/progress/${projectId}?token=${encodeURIComponent(auth.accessToken)}`
  let reconnectAttempts = 0
  const MAX_RECONNECT = 3
  let es = null

  function connect() {
    es = new EventSource(url)

    es.addEventListener('progress', (e) => {
      try {
        const data = JSON.parse(e.data)
        onProgress(data)
      } catch {}
    })

    es.addEventListener('keepalive', () => {
      reconnectAttempts = 0
    })

    es.addEventListener('done', (e) => {
      es.close()
      try {
        const data = JSON.parse(e.data)
        onDone(data)
      } catch {
        onDone({})
      }
    })

    es.addEventListener('error', (e) => {
      es.close()
      try {
        if (e.data) {
          const data = JSON.parse(e.data)
          onError(data)
          return
        }
      } catch {}

      reconnectAttempts++
      if (reconnectAttempts <= MAX_RECONNECT) {
        setTimeout(connect, 2000)
        onProgress({ progress: 0, msg: `连接断开，正在重试 (${reconnectAttempts}/${MAX_RECONNECT})...` })
      } else {
        onError({ msg: '连接超时。分析可能仍在后台进行，请稍后刷新页面查看结果。' })
      }
    })

    es.onerror = () => {}
  }

  connect()
  return {
    close: () => { if (es) es.close() }
  }
}

export async function getReport(projectId) {
  const res = await authedFetch(`${BASE}/report/${projectId}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Report not found' }))
    throw new Error(err.detail || 'Report not found')
  }
  return res.json()
}

export async function listProjects() {
  const res = await authedFetch(`${BASE}/projects`)
  return res.json()
}

export async function streamQA(projectId, question, conversation, onToken, onDone, onError, sessionId = null) {
  const auth = useAuthStore()
  try {
    const res = await fetch(`${BASE}/qa`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${auth.accessToken}`
      },
      body: JSON.stringify({
        project_id: projectId,
        question,
        conversation,
        session_id: sessionId,
      })
    })
    if (!res.ok) {
      if (res.status === 401) {
        const ok = await auth.tryRefresh()
        if (ok) return streamQA(projectId, question, conversation, onToken, onDone, onError, sessionId)
      }
      throw new Error('QA failed')
    }
    // 后端通过 X-Session-Id 头把(可能新建的)会话 id 透回来
    const newSessionId = res.headers.get('X-Session-Id') || sessionId
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      onToken(decoder.decode(value, { stream: true }))
    }
    onDone(newSessionId)
  } catch (e) {
    onError(e.message)
  }
}

// ────────────── QA 会话管理 ──────────────

export async function listQASessions(projectId) {
  const res = await authedFetch(`${BASE}/qa/sessions?project_id=${encodeURIComponent(projectId)}`)
  if (!res.ok) throw new Error('加载会话列表失败')
  return res.json()
}

export async function createQASession(projectId, title = null) {
  const res = await authedFetch(`${BASE}/qa/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, title })
  })
  if (!res.ok) throw new Error('新建会话失败')
  return res.json()
}

export async function getQAMessages(sessionId) {
  const res = await authedFetch(`${BASE}/qa/sessions/${sessionId}/messages`)
  if (!res.ok) throw new Error('加载历史失败')
  return res.json()
}

export async function renameQASession(sessionId, title) {
  const res = await authedFetch(`${BASE}/qa/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  })
  if (!res.ok) throw new Error('重命名失败')
  return res.json()
}

export async function deleteQASession(sessionId) {
  const res = await authedFetch(`${BASE}/qa/sessions/${sessionId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('删除会话失败')
  return res.json()
}

export async function deleteProject(projectId) {
  const res = await authedFetch(`${BASE}/projects/${projectId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Delete failed')
  return res.json()
}
