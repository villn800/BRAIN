import { useState } from 'react'
import { api } from '../lib/api'

export default function XImportForm({ onItemCreated }) {
  const [url, setUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)
    if (!url) {
      setError('Paste a tweet/X URL to import.')
      return
    }
    setSubmitting(true)
    try {
      const item = await api.createItemFromUrl({ url: url.trim() })
      setUrl('')
      setSuccess('Imported from X!')
      onItemCreated?.(item)
    } catch (exc) {
      const detail = exc?.data?.detail || exc.message || 'Import failed'
      setError(detail)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="action-card" onSubmit={handleSubmit}>
      <div>
        <h3>Import from X</h3>
        <p className="muted">Drop a tweet link and we’ll pull the media and text.</p>
      </div>
      <label className="field">
        <span>Tweet URL</span>
        <input
          type="url"
          name="x-url"
          placeholder="https://x.com/user/status/123..."
          value={url}
          onChange={(event) => setUrl(event.target.value)}
        />
      </label>
      {error && <p className="error-text">{error}</p>}
      {success && <p className="success-text">{success}</p>}
      <button type="submit" disabled={submitting}>
        {submitting ? 'Importing…' : 'Import from X'}
      </button>
    </form>
  )
}
