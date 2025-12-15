import { buildAssetUrl } from '../lib/assets'

function formatTweetDate(value) {
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

function parseAuthor(extraAuthor, sourceUrl) {
  let name = extraAuthor?.trim() || ''
  let handle = ''
  if (extraAuthor) {
    const match = extraAuthor.match(/^(.*?)\s*\(@?([^()\s]+)\)\s*$/)
    if (match) {
      name = match[1]?.trim() || ''
      handle = match[2]?.replace(/^@/, '') || ''
    }
  }

  if (!handle && sourceUrl) {
    try {
      const parsed = new URL(sourceUrl)
      const [maybeHandle] = parsed.pathname.split('/').filter(Boolean)
      handle = maybeHandle || ''
    } catch {
      handle = ''
    }
  }

  if (!name) {
    name = handle || 'Tweet'
  }

  return { name, handle }
}

export default function TweetCard({ item }) {
  const { name, handle } = parseAuthor(item?.extra?.author, item?.source_url)
  const avatarUrl = buildAssetUrl(item?.extra?.avatar_url)
  const fallbackInitial = (name || handle || '?').charAt(0).toUpperCase()
  const tweetDate = formatTweetDate(item?.extra?.timestamp || item?.created_at)
  const text = item?.description || item?.title || 'Open on X'
  const mediaCandidate = buildAssetUrl(item?.thumbnail_path || item?.file_path)
  const hideMedia = item?.extra?.primary_image_is_avatar === true
  const mediaUrl = !hideMedia ? mediaCandidate : null
  const verified = Boolean(item?.extra?.verified || item?.extra?.is_verified)

  const metrics = [
    { key: 'replies', value: item?.extra?.reply_count ?? item?.extra?.replies, label: 'Replies' },
    { key: 'retweets', value: item?.extra?.retweet_count ?? item?.extra?.reposts, label: 'Retweets' },
    { key: 'likes', value: item?.extra?.like_count ?? item?.extra?.favorite_count, label: 'Likes' },
    { key: 'views', value: item?.extra?.view_count ?? item?.extra?.views, label: 'Views' },
  ]
    .filter((entry) => entry.value !== undefined && entry.value !== null)
    .map((entry) => ({
      ...entry,
      formatted: new Intl.NumberFormat(undefined, { notation: 'compact' }).format(entry.value),
    }))

  return (
    <div className="tweet-card">
      <div className="tweet-card-header">
        <div className="tweet-card-avatar" aria-hidden={!avatarUrl}>
          {avatarUrl ? (
            <img src={avatarUrl} alt={name} loading="lazy" />
          ) : (
            <div className="tweet-card-avatar-fallback" aria-label="Tweet author">
              {fallbackInitial}
            </div>
          )}
        </div>
        <div className="tweet-card-author">
          <div className="tweet-card-name-row">
            <span className="tweet-card-name">{name}</span>
            {verified ? (
              <span className="tweet-card-verified" aria-label="Verified account">
                <svg viewBox="0 0 24 24" role="presentation" aria-hidden="true">
                  <circle cx="12" cy="12" r="12" />
                  <path d="M17 8.5 10.5 15 7 11.5" />
                </svg>
              </span>
            ) : null}
            {handle ? <span className="tweet-card-handle">@{handle}</span> : null}
          </div>
          {tweetDate ? <span className="tweet-card-date">{tweetDate}</span> : null}
        </div>
      </div>
      <p className="tweet-card-text" title={text}>
        {text}
      </p>
      {mediaUrl ? (
        <div className="tweet-card-media">
          <img src={mediaUrl} alt={text || 'Tweet media'} loading="lazy" />
        </div>
      ) : null}
      {metrics.length ? (
        <div className="tweet-card-metrics" aria-label="Tweet engagement">
          {metrics.map((metric) => (
            <span key={metric.key} className="tweet-card-metric">
              <span className="tweet-card-metric-dot" aria-hidden="true" />
              {metric.formatted}
            </span>
          ))}
        </div>
      ) : null}
      <div className="tweet-card-footer">
        <span className="pill subtle-pill tweet-card-pill">Tweet</span>
        <span className="pill subtle-pill tweet-card-pill">x.com</span>
      </div>
    </div>
  )
}
