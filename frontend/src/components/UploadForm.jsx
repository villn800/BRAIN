import { useState } from 'react'
import { api } from '../lib/api'

const MAX_UPLOAD_BYTES = 25 * 1024 * 1024

export default function UploadForm({ onItemCreated }) {
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState('')
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [uploading, setUploading] = useState(false)

  const handleFileChange = (event) => {
    const nextFile = event.target.files?.[0]
    setFile(nextFile ?? null)
    setError(null)
    setSuccess(null)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)
    if (!file) {
      setError('Please pick an image or PDF to upload.')
      return
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      setError('File exceeds the 25 MB limit.')
      return
    }

    const formData = new FormData()
    formData.append('file', file)
    if (title.trim()) {
      formData.append('title', title.trim())
    }
    if (description.trim()) {
      formData.append('description', description.trim())
    }
    if (tags.trim()) {
      formData.append('tags_csv', tags.trim())
    }

    setUploading(true)
    try {
      const item = await api.uploadItem(formData)
      setTitle('')
      setDescription('')
      setTags('')
      setFile(null)
      setSuccess('Upload complete!')
      onItemCreated?.(item)
    } catch (exc) {
      const detail = exc?.data?.detail || exc.message || 'Upload failed'
      setError(detail)
    } finally {
      setUploading(false)
    }
  }

  return (
    <form className="action-card" onSubmit={handleSubmit}>
      <div>
        <h3>Upload a file</h3>
        <p className="muted">Images get thumbnails; PDFs get extracted text.</p>
      </div>
      <label className="field">
        <span>File</span>
        <input type="file" accept="image/*,.pdf" onChange={handleFileChange} />
        {file && (
          <small className="muted">
            {file.name} — {(file.size / 1024 / 1024).toFixed(1)} MB
          </small>
        )}
      </label>
      <label className="field">
        <span>Title</span>
        <input type="text" value={title} onChange={(event) => setTitle(event.target.value)} />
      </label>
      <label className="field">
        <span>Description</span>
        <textarea rows="2" value={description} onChange={(event) => setDescription(event.target.value)} />
      </label>
      <label className="field">
        <span>Tags (comma-separated)</span>
        <input type="text" value={tags} onChange={(event) => setTags(event.target.value)} />
      </label>
      {error && <p className="error-text">{error}</p>}
      {success && <p className="success-text">{success}</p>}
      <button type="submit" disabled={uploading}>
        {uploading ? 'Uploading…' : 'Upload file'}
      </button>
    </form>
  )
}
