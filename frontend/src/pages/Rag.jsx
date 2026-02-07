import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { ragQuery, uploadDocument, hasToken } from '../api'

export default function Rag() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(10)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadInfo, setUploadInfo] = useState(null)

  if (!hasToken()) {
    navigate('/login', { replace: true })
    return null
  }

  async function handleUpload(e) {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Please select a PDF file.')
      return
    }
    setError('')
    setUploading(true)
    try {
      const data = await uploadDocument(file)
      setUploadInfo({ namespace: data.namespace, uploadId: data.upload_id, filename: data.filename })
      setResult(null)
    } catch (err) {
      setError(err.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const data = await ragQuery(
        query,
        topK,
        uploadInfo?.namespace ?? null,
        uploadInfo?.uploadId ?? null
      )
      setResult(data)
    } catch (err) {
      setError(err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h2>RAG Query</h2>

      <div className="card">
        <h3>1. Upload medical PDF (query from this document only)</h3>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleUpload}
          style={{ display: 'none' }}
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
        >
          {uploading ? 'Uploading…' : 'Upload PDF'}
        </button>
        {uploadInfo && (
          <p className="success" style={{ marginTop: '0.5rem' }}>
            Using document: <strong>{uploadInfo.filename}</strong>. Questions will be answered only from this file. Out-of-scope or critical questions will be refused; you will be advised to consult a doctor.
          </p>
        )}
      </div>

      <div className="card">
        <h3>2. Ask a question</h3>
        <form onSubmit={handleSubmit}>
          <label>Question</label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={3}
            required
            placeholder="e.g. What are the eligibility criteria in this document?"
          />
          <label>Top K</label>
          <input
            type="number"
            min={1}
            max={20}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
          />
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={loading}>
            {loading ? 'Asking…' : 'Ask'}
          </button>
        </form>
        {!uploadInfo && (
          <p style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#666' }}>
            Upload a PDF above to scope answers to your document. Without an upload, the default index is used (if configured).
          </p>
        )}
      </div>

      {result && (
        <div className="card">
          <h3>Response</h3>
          {result.refused ? (
            <>
              <div className="error">Refused</div>
              <p>{result.message}</p>
              {result.reason && <p><small>Reason: {result.reason}</small></p>}
            </>
          ) : (
            <>
              <p><strong>Answer:</strong></p>
              <p style={{ whiteSpace: 'pre-wrap' }}>{result.answer}</p>
              {result.citations?.length > 0 && (
                <p><strong>Citations:</strong> {result.citations.map((c) => (typeof c === 'string' ? c : `${c.doc_name}${c.section ? ' §' + c.section : ''}${c.page ? ' p.' + c.page : ''}`)).join(', ')}</p>
              )}
              {result.limitations && <p><small>{result.limitations}</small></p>}
              <details>
                <summary>Raw response</summary>
                <pre>{JSON.stringify(result, null, 2)}</pre>
              </details>
            </>
          )}
        </div>
      )}
    </div>
  )
}
