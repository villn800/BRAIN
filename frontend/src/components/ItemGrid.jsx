import ItemCard from './ItemCard'

export default function ItemGrid({ items, loading }) {
  if (!items.length && !loading) {
    return (
      <div className="empty-state">
        <h3>No items yet</h3>
        <p>Save a link or upload a file to populate your inspiration vault.</p>
      </div>
    )
  }

  return (
    <div className="item-grid">
      {items.map((item) => (
        <ItemCard key={item.id} item={item} />
      ))}
    </div>
  )
}
