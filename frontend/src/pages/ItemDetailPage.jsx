import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import { buildAssetUrl } from '../lib/assets'
import { getPosterSrc, getVideoSrc, isVideoItem } from '../lib/media'

export default function ItemDetailPage() {
  const { itemId } = useParams()
  const navigate = useNavigate()
  const [item, setItem] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    setLoading(true)
    api
      .getItem(itemId)
      .then((data) => {
        if (!active) {
          return
        }
        setItem(data)
        setError(null)
      })
      .catch((exc) => {
        if (!active) {
          return
        }
        setError(exc.message || 'Unable to load item')
      })
      .finally(() => {
        if (active) {
          setLoading(false)
        }
      })
    return () => {
      active = false
    }
  }, [itemId])

  useEffect(() => {
    if (item?.title) {
      document.title = `BRAIN — ${item.title}`
    } else {
      document.title = 'BRAIN — Item'
    }
  }, [item])

  if (loading) {
    return <div className="loading-row">Loading item…</div>
  }

  if (error) {
    return (
      <div className="detail-page">
        <div className="error-banner">
          <span>{error}</span>
          <button type="button" className="ghost" onClick={() => navigate('/')}>Go back</button>
        </div>
      </div>
    )
  }

  if (!item) {
    return null
  }

  const isVideo = isVideoItem(item)
  const posterUrl = getPosterSrc(item)
  const videoUrl = getVideoSrc(item)
  const previewUrl = posterUrl || buildAssetUrl(item.thumbnail_path || item.file_path)
  const downloadUrl = buildAssetUrl(item.file_path)

  return (
    <div className="detail-page">
      <div className="detail-header">
        <button type="button" className="ghost" onClick={() => navigate(-1)}>
          ← Back
        </button>
        <div>
          <p className="pill">{item.type}</p>
          <h1>{item.title}</h1>
          {item.origin_domain && <p className="muted">{item.origin_domain}</p>}
        </div>
        <div className="detail-actions">
          {item.source_url && (
            <a className="ghost" href={item.source_url} target="_blank" rel="noreferrer">
              Open source ↗
            </a>
          )}
          {downloadUrl && (
            <a className="ghost" href={downloadUrl} target="_blank" rel="noreferrer">
              Download asset
            </a>
          )}
        </div>
      </div>

      <div className="detail-meta-bar">
        <span className="pill subtle-pill">{item.origin_domain || item.type}</span>
        <span className="pill subtle-pill">{formatDate(item.created_at)}</span>
        {item.tags?.length ? (
          <span className="pill subtle-pill">
            {item.tags.length} tag{item.tags.length === 1 ? '' : 's'}
          </span>
        ) : null}
      </div>

      {(isVideo || previewUrl) && (
        <div className="detail-preview">
          {isVideo && videoUrl ? (
            <video
              className="detail-video"
              src={videoUrl}
              poster={posterUrl || undefined}
              controls
              playsInline
              preload="metadata"
            >
              Your browser does not support video playback.
            </video>
          ) : (
            previewUrl && <img src={previewUrl} alt={item.title} />
          )}
        </div>
      )}

      <section className="detail-section">
        <h3>Description</h3>
        <p>{item.description || 'No description provided.'}</p>
      </section>

      {item.text_content && (
        <section className="detail-section">
          <h3>Extracted text</h3>
          <pre className="text-preview">{item.text_content}</pre>
        </section>
      )}

      <section className="detail-section">
        <h3>Metadata</h3>
        <dl className="meta-grid">
          <div>
            <dt>Created</dt>
            <dd>{formatDate(item.created_at)}</dd>
          </div>
          <div>
            <dt>Updated</dt>
            <dd>{formatDate(item.updated_at)}</dd>
          </div>
          {item.origin_domain && (
            <div>
              <dt>Domain</dt>
              <dd>{item.origin_domain}</dd>
            </div>
          )}
          {item.file_size_bytes && (
            <div>
              <dt>File size</dt>
              <dd>{formatBytes(item.file_size_bytes)}</dd>
            </div>
          )}
          {item.status && (
            <div>
              <dt>Status</dt>
              <dd>{item.status}</dd>
            </div>
          )}
        </dl>
      </section>

      {item.tags?.length ? (
        <section className="detail-section">
          <h3>Tags</h3>
          <div className="tag-row">
            {item.tags.map((tag) => (
              <span key={tag.id} className="tag-pill">
                {tag.name}
              </span>
            ))}
          </div>
        </section>
      ) : null}

      <footer className="detail-footer">
        <Link to="/" className="ghost">
          ← Back to grid
        </Link>
      </footer>
    </div>
  )
}

function formatDate(value) {
  if (!value) {
    return '—'
  }
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value))
  } catch {
    return value
  }
}

function formatBytes(bytes) {
  if (!bytes) {
    return '—'
  }
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`
}
