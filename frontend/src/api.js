/**
 * API client for Healthcare RAG Backend.
 * Base URL: same origin in dev (Vite proxy /api -> backend) or set VITE_API_URL.
 */
const BASE = import.meta.env.VITE_API_URL || ''

function getAccessToken() {
  return localStorage.getItem('access_token')
}

function getAuthHeaders() {
  const token = getAccessToken()
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

export async function health() {
  const r = await fetch(`${BASE}/api/v1/health`)
  return r.json()
}

export async function ready() {
  const r = await fetch(`${BASE}/api/v1/ready`)
  return r.json()
}

export async function login(email, password) {
  const r = await fetch(`${BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(data.detail || data.message || 'Login failed')
  return data
}

export async function register(email, password, role, fullName) {
  const r = await fetch(`${BASE}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, role, full_name: fullName || null }),
  })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(data.detail || data.message || 'Registration failed')
  return data
}

export async function refreshTokens(refreshToken) {
  const r = await fetch(`${BASE}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(data.detail || 'Refresh failed')
  return data
}

export async function me() {
  const r = await fetch(`${BASE}/api/v1/auth/me`, { headers: getAuthHeaders() })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(data.detail || 'Not authenticated')
  return data
}

export async function uploadDocument(file) {
  const token = getAccessToken()
  if (!token) throw new Error('Not authenticated')
  const form = new FormData()
  form.append('file', file)
  const r = await fetch(`${BASE}/api/v1/documents/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(data.detail || data.message || 'Upload failed')
  return data
}

export async function ragQuery(query, topK = 10, namespace = null, uploadId = null) {
  const body = { query, top_k: topK, include_metadata: true }
  if (namespace) body.namespace = namespace
  if (uploadId) body.upload_id = uploadId
  const r = await fetch(`${BASE}/api/v1/rag/query`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  })
  const data = await r.json().catch(() => ({}))
  if (!r.ok && !data.refused) throw new Error(data.detail || 'Request failed')
  return data
}

export function setTokens(accessToken, refreshToken) {
  if (accessToken) localStorage.setItem('access_token', accessToken)
  if (refreshToken) localStorage.setItem('refresh_token', refreshToken)
}

export function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

export function hasToken() {
  return !!getAccessToken()
}
