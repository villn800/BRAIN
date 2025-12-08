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
  const isVideo = item?.extra?.media_kind === 'video' || Boolean(item?.extra?.video_url)
   const isHlsOnly = Boolean(item?.extra?.twitter_hls_only) && !isVideo
  const overlayMeta = [
    item.origin_domain || item.type,
    item.tags?.[0]?.name || formatDate(item.created_at),
  ]
    .filter(Boolean)
    .slice(0, 2)
    .join(' • ')
  const overlayHint =
    item.description && item.description.length > 140
      ? `${item.description.slice(0, 140)}…`
      : item.description || overlayMeta || 'Open to see details'
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
        {isVideo ? (
          <span className="video-badge" data-testid="video-badge">
            <span className="video-badge-icon" aria-hidden="true" />
            Video
          </span>
        ) : null}
        {!isVideo && isHlsOnly ? (
          <span className="video-badge hls-only" data-testid="video-on-x-badge">
            <span className="video-badge-icon" aria-hidden="true" />
            Video on X
          </span>
        ) : null}
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
            <span className="overlay-meta">{overlayMeta}</span>
          </div>
          <div className="overlay-bottom">
            <p className="overlay-title" title={item.title}>
              {item.title}
            </p>
            <p className="overlay-hint">{overlayHint}</p>
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
