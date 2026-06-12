const BASE = '/api/auth'

async function handleAuthResponse(res) {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export async function register(username, email, password) {
  const res = await fetch(`${BASE}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password })
  })
  return handleAuthResponse(res)
}

export async function login(email, password) {
  const res = await fetch(`${BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  return handleAuthResponse(res)
}

export async function refresh(refreshToken) {
  const res = await fetch(`${BASE}/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  })
  return handleAuthResponse(res)
}

export async function logout() {
  try {
    await fetch(`${BASE}/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
  } catch {
    // 忽略网络错误
  }
}

export async function fetchMe(accessToken) {
  const res = await fetch(`${BASE}/me`, {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  })
  if (!res.ok) throw new Error('Not authenticated')
  return res.json()
}
