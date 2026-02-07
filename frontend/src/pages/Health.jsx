import { useState, useEffect } from 'react'
import { health, ready } from '../api'

export default function Health() {
  const [healthRes, setHealthRes] = useState(null)
  const [readyRes, setReadyRes] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function run() {
      try {
        const [h, r] = await Promise.all([health(), ready()])
        if (!cancelled) {
          setHealthRes(h)
          setReadyRes(r)
        }
      } catch (err) {
        if (!cancelled) setError(err.message || 'Failed to fetch')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="container"><p>Loading…</p></div>
  if (error) return <div className="container"><div className="error">{error}</div></div>

  return (
    <div className="container">
      <h2>Backend Health</h2>
      <div className="card">
        <h3>GET /api/v1/health</h3>
        <pre>{JSON.stringify(healthRes, null, 2)}</pre>
      </div>
      <div className="card">
        <h3>GET /api/v1/ready</h3>
        <pre>{JSON.stringify(readyRes, null, 2)}</pre>
      </div>
    </div>
  )
}
