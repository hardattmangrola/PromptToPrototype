import { Link } from 'react-router-dom'
import { hasToken } from '../api'

export default function Home() {
  return (
    <div className="container">
      <h2>Healthcare RAG – Test Frontend</h2>
      <p>Use this app to test backend: auth, health, and RAG query.</p>
      <ul>
        <li><Link to="/health">Health &amp; Ready</Link> – Check backend liveness and DB</li>
        <li><Link to="/login">Login</Link> – Get access token</li>
        <li><Link to="/register">Register</Link> – Create patient/doctor account</li>
        {hasToken() ? (
          <li><Link to="/rag">RAG Query</Link> – Ask a question (authenticated)</li>
        ) : (
          <li>Log in to use <Link to="/rag">RAG Query</Link></li>
        )}
      </ul>
    </div>
  )
}
