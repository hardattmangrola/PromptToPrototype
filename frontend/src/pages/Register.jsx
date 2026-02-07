import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register, setTokens } from '../api'

export default function Register() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('patient')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await register(email, password, role, fullName || null)
      if (data.id) {
        setTokens(null, null)
        navigate('/login', { replace: true })
      }
    } catch (err) {
      setError(err.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <div className="card">
        <h2>Register</h2>
        <form onSubmit={handleSubmit}>
          <label>Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <label>Password (min 8)</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required />
          <label>Role</label>
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="patient">Patient</option>
            <option value="doctor">Doctor</option>
          </select>
          <label>Full name (optional)</label>
          <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={loading}>{loading ? 'Registering…' : 'Register'}</button>
        </form>
        <p><Link to="/login">Login</Link> if you already have an account.</p>
      </div>
    </div>
  )
}
