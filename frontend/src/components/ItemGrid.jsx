import ItemCard from './ItemCard'

export default function ItemGrid({ items, loading, onSelectItem, gridStyle, overlayMode = 'hover' }) {
  if (!items.length && !loading) {
    return (
      <div className="empty-state">
        <h3>No items yet</h3>
        <p>Save a link or upload a file to populate your inspiration vault.</p>
      </div>
    )
  }

  return (
    <div className="masonry-grid" style={gridStyle}>
      {items.map((item) => (
        <ItemCard key={item.id} item={item} onSelect={onSelectItem} overlayMode={overlayMode} />
      ))}
      {loading && <div className="masonry-loader">Loading…</div>}
    </div>
  )
}
