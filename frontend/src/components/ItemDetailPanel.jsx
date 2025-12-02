import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { createPortal } from 'react-dom'
import { api } from '../lib/api'
import { buildAssetUrl } from '../lib/assets'

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

export default function ItemDetailPanel({ itemId, onClose }) {
  const [item, setItem] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const panelRef = useRef(null)

  useEffect(() => {
    if (!itemId) {
      return
    }
    let active = true
    setLoading(true)
    setError(null)
    setItem(null)
    api
      .getItem(itemId)
      .then((data) => {
        if (!active) {
          return
        }
        setItem(data)
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
    const handleKey = (event) => {
      if (event.key === 'Escape') {
        onClose?.()
      }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose])

  useEffect(() => {
    panelRef.current?.focus()
  }, [itemId])

  useEffect(() => {
    if (!itemId) {
      return
    }
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = previousOverflow
    }
  }, [itemId])

  useEffect(() => {
    const node = panelRef.current
    if (!node) {
      return
    }
    const handleTrap = (event) => {
      if (event.key !== 'Tab') {
        return
      }
      const focusable = node.querySelectorAll(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
      )
      const entries = Array.from(focusable)
      if (!entries.length) {
        event.preventDefault()
        node.focus()
        return
      }
      const first = entries[0]
      const last = entries[entries.length - 1]
      if (event.shiftKey) {
        if (document.activeElement === first) {
          event.preventDefault()
          last.focus()
        }
      } else if (document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    node.addEventListener('keydown', handleTrap)
    return () => node.removeEventListener('keydown', handleTrap)
  }, [item])

  if (!itemId) {
    return null
  }

  const previewUrl = buildAssetUrl(item?.thumbnail_path || item?.file_path)
  const downloadUrl = buildAssetUrl(item?.file_path)

  const content = (
    <div className="detail-overlay" onClick={onClose}>
      <div
        className="detail-panel"
        role="dialog"
        aria-modal="true"
        aria-label={item?.title || 'Item details'}
        tabIndex={-1}
        ref={panelRef}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="detail-panel-header">
          <div>
            <p className="pill">{item?.type || 'Item'}</p>
            <h2>{item?.title || 'Loading…'}</h2>
            {item?.origin_domain && <p className="muted">{item.origin_domain}</p>}
          </div>
          <div className="detail-panel-actions">
            {item?.source_url && (
              <a className="ghost" href={item.source_url} target="_blank" rel="noreferrer">
                Open source ↗
              </a>
            )}
            {item?.id && (
              <Link className="ghost" to={`/items/${item.id}`}>
                Full view →
              </Link>
            )}
            {downloadUrl && (
              <a className="ghost" href={downloadUrl} target="_blank" rel="noreferrer">
                Download
              </a>
            )}
            <button type="button" className="ghost" onClick={onClose}>
              Close ✕
            </button>
          </div>
        </div>

        {loading && <div className="loading-row">Loading item…</div>}
        {error && <div className="error-banner">{error}</div>}

        {!loading && !error && item ? (
          <div className="detail-panel-body">
            {previewUrl && (
              <div className="detail-preview">
                <img src={previewUrl} alt={item.title} />
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
          </div>
        ) : null}
      </div>
    </div>
  )

  return createPortal(content, document.body)
}
