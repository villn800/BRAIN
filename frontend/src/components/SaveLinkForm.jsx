import { useState } from 'react'
import { api } from '../lib/api'

function parseTags(value) {
  if (!value) {
    return []
  }
  return value
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
}

export default function SaveLinkForm({ onItemCreated }) {
  const [formState, setFormState] = useState({ url: '', title: '', tags: '' })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)
    if (!formState.url) {
      setError('Please provide a URL to save.')
      return
    }
    setSubmitting(true)
    try {
      const item = await api.createItemFromUrl({
        url: formState.url.trim(),
        title: formState.title.trim() || undefined,
        tags: parseTags(formState.tags),
      })
      setFormState({ url: '', title: '', tags: '' })
      setSuccess('Link saved!')
      onItemCreated?.(item)
    } catch (exc) {
      const detail = exc?.data?.detail || exc.message || 'Unable to save link'
      setError(detail)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="action-card" onSubmit={handleSubmit}>
      <div>
        <h3>Save a link</h3>
        <p className="muted">Paste any URL (or Tweet / Pin) and we will pull metadata + previews.</p>
      </div>
      <label className="field">
        <span>URL</span>
        <input name="url" type="url" placeholder="https://" value={formState.url} onChange={handleChange} />
      </label>
      <label className="field">
        <span>Title (optional)</span>
        <input name="title" type="text" value={formState.title} onChange={handleChange} />
      </label>
      <label className="field">
        <span>Tags (comma-separated)</span>
        <input name="tags" type="text" placeholder="poster, mood" value={formState.tags} onChange={handleChange} />
      </label>
      {error && <p className="error-text">{error}</p>}
      {success && <p className="success-text">{success}</p>}
      <button type="submit" disabled={submitting}>
        {submitting ? 'Saving…' : 'Save link'}
      </button>
    </form>
  )
}
