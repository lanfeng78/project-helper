// 用户系统已移除——所有请求都是无鉴权的直连。
// 保留极小的 fetch 包装方便集中处理网络错误,主要是为了:
//   - 给 SSE / 流式 fetch 留一处统一的 BASE 拼接;
//   - 错误信息统一从 JSON 解析 detail,失败时退回 statusText。
const BASE = '/api'

async function jsonRequest(url, options = {}) {
  const res = await fetch(url, options)
  if (!res.ok) {
    let msg = res.statusText || 'Request failed'
    try {
      const err = await res.json()
      if (err && err.detail) msg = err.detail
    } catch { /* response not JSON, keep statusText */ }
    throw new Error(msg)
  }
  return res
}

export async function analyzeRepo(repoUrl, mode = 'detail') {
  const res = await jsonRequest(`${BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl, mode })
  })
  return res.json()
}

export function subscribeProgress(projectId, onProgress, onDone, onError) {
  const url = `${BASE}/progress/${projectId}`
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
  const res = await jsonRequest(`${BASE}/report/${projectId}`)
  return res.json()
}

export async function listProjects() {
  const res = await jsonRequest(`${BASE}/projects`)
  return res.json()
}

export async function streamQA(projectId, question, conversation, onToken, onDone, onError, sessionId = null) {
  try {
    const res = await fetch(`${BASE}/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_id: projectId,
        question,
        conversation,
        session_id: sessionId,
      })
    })
    if (!res.ok) {
      let msg = res.statusText || 'QA failed'
      try { const err = await res.json(); if (err && err.detail) msg = err.detail } catch {}
      throw new Error(msg)
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

export async function deleteProject(projectId) {
  const res = await jsonRequest(`${BASE}/projects/${projectId}`, { method: 'DELETE' })
  return res.json()
}

// ────────────── QA 会话管理 ──────────────

export async function listQASessions(projectId) {
  const res = await jsonRequest(`${BASE}/qa/sessions?project_id=${encodeURIComponent(projectId)}`)
  return res.json()
}

export async function createQASession(projectId, title = null) {
  const res = await jsonRequest(`${BASE}/qa/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, title })
  })
  return res.json()
}

export async function getQAMessages(sessionId) {
  const res = await jsonRequest(`${BASE}/qa/sessions/${sessionId}/messages`)
  return res.json()
}

export async function renameQASession(sessionId, title) {
  const res = await jsonRequest(`${BASE}/qa/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  })
  return res.json()
}

export async function deleteQASession(sessionId) {
  const res = await jsonRequest(`${BASE}/qa/sessions/${sessionId}`, { method: 'DELETE' })
  return res.json()
}
