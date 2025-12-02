import { Link } from 'react-router-dom'
import { buildAssetUrl } from '../lib/assets'

function formatDate(value) {
  if (!value) {
    return ''
  }
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(new Date(value))
  } catch {
    return value
  }
}

export default function ItemCard({ item, onSelect, overlayMode = 'hover' }) {
  const imageUrl = buildAssetUrl(item.thumbnail_path || item.file_path)
  const Tag = onSelect ? 'button' : Link
  const tagProps = onSelect
    ? {
        type: 'button',
        onClick: () => onSelect(item),
      }
    : { to: `/items/${item.id}` }

  const className = ['item-card', overlayMode === 'always' ? 'overlay-always' : ''].filter(Boolean).join(' ')

  return (
    <Tag className={className} aria-label={item.title} {...tagProps}>
      <div className="item-media">
        {imageUrl ? (
          <img src={imageUrl} alt={item.title} loading="lazy" />
        ) : (
          <div className="media-fallback">
            <span className="pill">{item.type}</span>
            <p>No preview</p>
          </div>
        )}
        <div className="card-overlay">
          <div className="overlay-top">
            <span className="pill subtle-pill">{item.origin_domain || item.type}</span>
            <span className="overlay-date">{formatDate(item.created_at)}</span>
          </div>
          <div className="overlay-bottom">
            <p className="overlay-title" title={item.title}>
              {item.title}
            </p>
            {item.tags?.length ? (
              <div className="overlay-tags">
                {item.tags.slice(0, 3).map((tag) => (
                  <span key={tag.id} className="tag-pill">
                    {tag.name}
                  </span>
                ))}
                {item.tags.length > 3 && (
                  <span className="tag-pill muted-pill">+{item.tags.length - 3}</span>
                )}
              </div>
            ) : (
              <p className="overlay-hint">Open to see details</p>
            )}
          </div>
        </div>
      </div>
      <div className="item-body">
        <p className="item-type">{item.origin_domain || item.type}</p>
        <h3 title={item.title}>{item.title}</h3>
        {item.description && <p className="item-description">{item.description}</p>}
        <div className="item-meta">
          <span>{formatDate(item.created_at)}</span>
          {item.tags?.length ? (
            <span>
              {item.tags.length} tag{item.tags.length === 1 ? '' : 's'}
            </span>
          ) : null}
        </div>
      </div>
    </Tag>
  )
}
