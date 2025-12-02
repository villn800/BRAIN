import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import ItemGrid from '../components/ItemGrid'
import ItemDetailPanel from '../components/ItemDetailPanel'
import SettingsModal from '../components/SettingsModal'
import SaveLinkForm from '../components/SaveLinkForm'
import SearchFilters from '../components/SearchFilters'
import UploadForm from '../components/UploadForm'
import { api } from '../lib/api'
import { useSettings } from '../context/SettingsContext'

const PAGE_SIZE = 24

const DEFAULT_FILTERS = {
  q: '',
  type: '',
  tags: [],
  createdFrom: '',
  createdTo: '',
}

export default function ItemsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [items, setItems] = useState([])
  const [filters, setFilters] = useState(() => ({ ...DEFAULT_FILTERS }))
  const [loading, setLoading] = useState(false)
  const [loadMoreLoading, setLoadMoreLoading] = useState(false)
  const [error, setError] = useState(null)
  const [hasMore, setHasMore] = useState(true)
  const [refreshToken, setRefreshToken] = useState(0)
  const [tags, setTags] = useState([])
  const [settingsOpen, setSettingsOpen] = useState(false)
  const { settings } = useSettings()

  const filtersKey = useMemo(() => JSON.stringify(filters), [filters])
  const selectedItemId = searchParams.get('itemId')

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

  const handleSelectItem = (item) => {
    const next = new URLSearchParams(searchParams)
    next.set('itemId', item.id)
    setSearchParams(next, { replace: false })
  }

  const handleClosePanel = () => {
    const next = new URLSearchParams(searchParams)
    next.delete('itemId')
    setSearchParams(next, { replace: true })
  }

  const columnWidth = {
    compact: 240,
    cozy: 280,
    airy: 320,
  }[settings.gridDensity]

  const thumbHeight = {
    small: 180,
    medium: 230,
    large: 300,
  }[settings.thumbSize]

  const gridStyle = {
    '--masonry-column-width': `${columnWidth}px`,
    '--masonry-gap':
      settings.gridDensity === 'compact' ? '0.9rem' : settings.gridDensity === 'airy' ? '1.4rem' : '1.1rem',
    '--thumb-min-height': `${thumbHeight}px`,
  }

  const pageClassNames = [
    'board-page',
    `density-${settings.gridDensity}`,
    `theme-${settings.themeIntensity}`,
    `motion-${settings.motion}`,
    `overlay-${settings.overlayMode}`,
  ].join(' ')

  return (
    <div className={pageClassNames}>
      <div className="board-backdrop" aria-hidden />
      <div className="board-layout">
        <aside className="command-rail">
          <div className="rail-title">
            <p className="eyebrow">Inputs</p>
            <h3>Search, save, upload</h3>
            <p className="muted">Pinned controls stay put while the board flows.</p>
          </div>
          <div className="rail-scroll">
            <SearchFilters
              filters={filters}
              onFiltersChange={handleFiltersChange}
              onReset={handleResetFilters}
              availableTags={tags}
            />
            <SaveLinkForm onItemCreated={handleItemCreated} />
            <UploadForm onItemCreated={handleItemCreated} />
          </div>
        </aside>

        <section className="board-main">
          <div className="board-top">
            <div>
              <p className="eyebrow">Inspiration board</p>
              <h1>Studio masonry view</h1>
              <p className="muted">High-density, flowing tiles kept above the fold with hover metadata.</p>
              <div className="board-meta">
                <span className="pill subtle-pill">{settings.gridDensity} density</span>
                <span className="pill subtle-pill">{settings.thumbSize} thumbs</span>
                <span className="pill subtle-pill">
                  {settings.overlayMode === 'hover' ? 'Overlay on hover' : 'Overlay always'}
                </span>
              </div>
            </div>
            <div className="board-actions">
              <button type="button" className="ghost" onClick={handleRefresh}>
                Refresh ↻
              </button>
              <button type="button" className="ghost" onClick={() => setSettingsOpen(true)}>
                Settings ⚙︎
              </button>
            </div>
          </div>

          {error && (
            <div className="error-banner">
              <span>{error}</span>
              <button type="button" className="ghost" onClick={handleRefresh}>
                Retry
              </button>
            </div>
          )}

          <ItemGrid
            items={items}
            loading={loading}
            onSelectItem={handleSelectItem}
            gridStyle={gridStyle}
            overlayMode={settings.overlayMode}
          />

          {hasMore && !loading && (
            <div className="load-more">
              <button type="button" onClick={handleLoadMore} disabled={loadMoreLoading}>
                {loadMoreLoading ? 'Loading…' : 'Load more'}
              </button>
            </div>
          )}
        </section>

        {selectedItemId && <ItemDetailPanel itemId={selectedItemId} onClose={handleClosePanel} />}
        <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      </div>
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
