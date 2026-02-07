/**
 * API Service - Centralized HTTP client with JWT handling
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

class ApiService {
    constructor() {
        this.accessToken = localStorage.getItem('access_token')
        this.refreshToken = localStorage.getItem('refresh_token')
    }

    setTokens(access, refresh) {
        this.accessToken = access
        this.refreshToken = refresh
        localStorage.setItem('access_token', access)
        localStorage.setItem('refresh_token', refresh)
    }

    clearTokens() {
        this.accessToken = null
        this.refreshToken = null
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
    }

    async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`
        const headers = { 'Content-Type': 'application/json', ...options.headers }

        if (this.accessToken && !options.skipAuth) {
            headers['Authorization'] = `Bearer ${this.accessToken}`
        }

        try {
            const response = await fetch(url, { ...options, headers })

            // Try refresh if 401
            if (response.status === 401 && this.refreshToken && !options._retry) {
                const refreshed = await this.refreshAccessToken()
                if (refreshed) {
                    return this.request(endpoint, { ...options, _retry: true })
                }
            }

            const data = await response.json().catch(() => ({}))

            if (!response.ok) {
                throw new Error(data.detail || data.message || `HTTP ${response.status}`)
            }

            return data
        } catch (error) {
            if (error.message.includes('fetch')) {
                throw new Error('Backend unavailable')
            }
            throw error
        }
    }

    async refreshAccessToken() {
        try {
            const response = await fetch(`${API_BASE}/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: this.refreshToken }),
            })

            if (response.ok) {
                const data = await response.json()
                this.setTokens(data.access_token, data.refresh_token)
                return true
            }
        } catch {
            // Refresh failed
        }
        this.clearTokens()
        return false
    }

    // Auth
    async login(email, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
            skipAuth: true,
        })
        this.setTokens(data.access_token, data.refresh_token)
        return data
    }

    async register(email, password, role, fullName) {
        const data = await this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password, role, full_name: fullName }),
            skipAuth: true,
        })
        // Auto-login after register
        return this.login(email, password)
    }

    async getMe() {
        return this.request('/auth/me')
    }

    // RAG
    async query(queryText, options = {}) {
        return this.request('/rag/query', {
            method: 'POST',
            body: JSON.stringify({
                query: queryText,
                top_k: options.topK || 5,
                upload_id: options.uploadId,
                namespace: options.namespace,
                context: options.context, // NEW: Patient context
            }),
        })
    }

    // Documents
    async uploadDocument(file) {
        const formData = new FormData()
        formData.append('file', file)

        const url = `${API_BASE}/documents/upload`
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${this.accessToken}` },
            body: formData,
        })

        const data = await response.json().catch(() => ({}))
        if (!response.ok) {
            throw new Error(data.detail || 'Upload failed')
        }
        return data
    }
}

export const api = new ApiService()
export default api
