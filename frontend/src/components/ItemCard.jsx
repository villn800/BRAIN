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

function extractTwitterHandle(url) {
  if (!url) {
    return ''
  }
  try {
    const parsed = new URL(url)
    const [handle] = parsed.pathname.split('/').filter(Boolean)
    return handle || ''
  } catch {
    return ''
  }
}

export default function ItemCard({ item, onSelect, overlayMode = 'hover' }) {
  const imageUrl = buildAssetUrl(item.thumbnail_path || item.file_path)
  const isVideo = item?.extra?.media_kind === 'video' || Boolean(item?.extra?.video_url)
  const isHlsOnly = Boolean(item?.extra?.twitter_hls_only) && !isVideo
  const isTwitter =
    (item?.origin_domain || '').includes('twitter.com') ||
    (item?.origin_domain || '').includes('x.com') ||
    (item?.source_url || '').includes('twitter.com') ||
    (item?.source_url || '').includes('x.com')
  const hasPreview = Boolean(imageUrl)
  const showTweetCard = isTwitter && !isVideo
  const tweetHandle = extractTwitterHandle(item?.source_url || '') || item?.extra?.twitter_handle || ''
  const tweetAvatar = buildAssetUrl(item?.extra?.twitter_avatar)
  const tweetAuthor = item?.extra?.twitter_author || tweetHandle || 'Tweet'
  const tweetText = item?.title || item?.description || 'View on X'
  const tweetDate = formatDate(item?.created_at)
  const isAvatarPreview = Boolean(tweetAvatar && imageUrl && tweetAvatar === imageUrl)
  const showTweetMedia = hasPreview && !isAvatarPreview
  const tweetMediaUrl = showTweetMedia ? imageUrl : null
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
        {isVideo ? (
          hasPreview ? (
            <img src={imageUrl} alt={item.title} loading="lazy" />
          ) : (
            <div className="media-fallback">
              <span className="pill">{item.type}</span>
              <p>No preview</p>
            </div>
          )
        ) : showTweetCard ? (
          <div className="tweet-fallback" aria-label="Tweet preview">
            <div className="tweet-fallback-top">
              <span className="tweet-pill">tweet</span>
              <span className="tweet-source chip">X.com</span>
            </div>
            <div className="tweet-fallback-author">
              {tweetAvatar ? (
                <img className="tweet-avatar" src={tweetAvatar} alt={tweetAuthor} loading="lazy" />
              ) : (
                <div className="tweet-avatar placeholder" aria-hidden="true" />
              )}
              <div>
                <div className="tweet-name">{tweetAuthor}</div>
                {tweetHandle ? <div className="tweet-handle">@{tweetHandle}</div> : null}
              </div>
            </div>
            <p className="tweet-text" title={tweetText}>
              {tweetText}
            </p>
            {tweetMediaUrl ? (
              <div className="tweet-media-thumb">
                <img src={tweetMediaUrl} alt={tweetText} loading="lazy" />
              </div>
            ) : null}
            <div className="tweet-meta">
              {tweetDate ? <span className="tweet-date">{tweetDate}</span> : null}
              <span className="tweet-open">Open on X ↗</span>
            </div>
          </div>
        ) : (
          hasPreview ? (
            <img src={imageUrl} alt={item.title} loading="lazy" />
          ) : (
            <div className="media-fallback">
              <span className="pill">{item.type}</span>
              <p>No preview</p>
            </div>
          )
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
