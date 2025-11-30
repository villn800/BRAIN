import { useEffect, useMemo, useState } from 'react'
import ItemGrid from '../components/ItemGrid'
import SaveLinkForm from '../components/SaveLinkForm'
import SearchFilters from '../components/SearchFilters'
import UploadForm from '../components/UploadForm'
import { api } from '../lib/api'

const PAGE_SIZE = 24

const DEFAULT_FILTERS = {
  q: '',
  type: '',
  tags: [],
  createdFrom: '',
  createdTo: '',
}

export default function ItemsPage() {
  const [items, setItems] = useState([])
  const [filters, setFilters] = useState(() => ({ ...DEFAULT_FILTERS }))
  const [loading, setLoading] = useState(false)
  const [loadMoreLoading, setLoadMoreLoading] = useState(false)
  const [error, setError] = useState(null)
  const [hasMore, setHasMore] = useState(true)
  const [refreshToken, setRefreshToken] = useState(0)
  const [tags, setTags] = useState([])

  const filtersKey = useMemo(() => JSON.stringify(filters), [filters])

  useEffect(() => {
    let cancelled = false
    api
      .getTags()
      .then((data) => {
        if (!cancelled) {
          setTags(data)
        }
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)

    api
      .getItems(buildQueryParams(filters, 0), { signal: controller.signal })
      .then((data) => {
        setItems(data)
        setHasMore(data.length === PAGE_SIZE)
      })
      .catch((exc) => {
        if (exc.name === 'AbortError') {
          return
        }
        setError(exc.message || 'Failed to load items')
      })
      .finally(() => {
        setLoading(false)
      })

    return () => controller.abort()
  }, [filtersKey, refreshToken])

  const handleFiltersChange = (nextFilters) => {
    setFilters({ ...nextFilters })
  }

  const handleResetFilters = () => {
    setFilters({ ...DEFAULT_FILTERS })
  }

  const handleRefresh = () => {
    setError(null)
    setRefreshToken((token) => token + 1)
  }

  const handleLoadMore = async () => {
    if (loadMoreLoading) {
      return
    }
    setLoadMoreLoading(true)
    setError(null)
    try {
      const data = await api.getItems(buildQueryParams(filters, items.length))
      setItems((prev) => [...prev, ...data])
      setHasMore(data.length === PAGE_SIZE)
    } catch (exc) {
      setError(exc.message || 'Failed to load more items')
    } finally {
      setLoadMoreLoading(false)
    }
  }

  const handleItemCreated = (item) => {
    setError(null)
    setItems((prev) => [item, ...prev])
  }

  return (
    <div className="items-page">
      <div className="grid-header">
        <div>
          <h1>Saved inspiration</h1>
          <p className="muted">Browse, search, and add ideas without leaving your flow.</p>
        </div>
        <button type="button" className="ghost" onClick={handleRefresh}>
          Refresh
        </button>
      </div>

      <div className="actions-grid">
        <SearchFilters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onReset={handleResetFilters}
          availableTags={tags}
        />
        <SaveLinkForm onItemCreated={handleItemCreated} />
        <UploadForm onItemCreated={handleItemCreated} />
      </div>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button type="button" className="ghost" onClick={handleRefresh}>
            Retry
          </button>
        </div>
      )}

      {loading && <div className="loading-row">Loading items…</div>}

      <ItemGrid items={items} loading={loading} />

      {hasMore && !loading && (
        <div className="load-more">
          <button type="button" onClick={handleLoadMore} disabled={loadMoreLoading}>
            {loadMoreLoading ? 'Loading…' : 'Load more'}
          </button>
        </div>
      )}
    </div>
  )
}

function buildQueryParams(filters, offset) {
  const params = {
    limit: PAGE_SIZE,
    offset,
  }

  if (filters.q) {
    params.q = filters.q
  }
  if (filters.type) {
    params.type = filters.type
  }
  if (filters.tags?.length) {
    params.tags = filters.tags
  }
  if (filters.createdFrom) {
    const fromIso = toIsoStart(filters.createdFrom)
    if (fromIso) {
      params.created_from = fromIso
    }
  }
  if (filters.createdTo) {
    const toIso = toIsoEnd(filters.createdTo)
    if (toIso) {
      params.created_to = toIso
    }
  }

  return params
}

function toIsoStart(dateString) {
  try {
    const value = new Date(`${dateString}T00:00:00Z`)
    return Number.isNaN(value.getTime()) ? null : value.toISOString()
  } catch {
    return null
  }
}

function toIsoEnd(dateString) {
  try {
    const value = new Date(`${dateString}T23:59:59Z`)
    return Number.isNaN(value.getTime()) ? null : value.toISOString()
  } catch {
    return null
  }
}
