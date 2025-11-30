const ITEM_TYPES = [
  { value: '', label: 'All types' },
  { value: 'url', label: 'Link' },
  { value: 'tweet', label: 'Tweet' },
  { value: 'pin', label: 'Pin' },
  { value: 'image', label: 'Image' },
  { value: 'pdf', label: 'PDF' },
  { value: 'note', label: 'Note' },
  { value: 'other', label: 'Other' },
]

export default function SearchFilters({ filters, onFiltersChange, onReset, availableTags }) {
  const handleInputChange = (event) => {
    const { name, value } = event.target
    onFiltersChange({ ...filters, [name]: value })
  }

  const handleTagChange = (event) => {
    const selected = Array.from(event.target.selectedOptions).map((option) => option.value)
    onFiltersChange({ ...filters, tags: selected })
  }

  return (
    <div className="filters-card">
      <div>
        <h3>Search & Filters</h3>
        <p className="muted">Combine filters to zero in on the exact inspiration you need.</p>
      </div>
      <div className="filters-grid">
        <label className="field">
          <span>Keyword</span>
          <input
            type="search"
            name="q"
            placeholder="poster, typography, mood…"
            value={filters.q}
            onChange={handleInputChange}
          />
        </label>
        <label className="field">
          <span>Type</span>
          <select name="type" value={filters.type} onChange={handleInputChange}>
            {ITEM_TYPES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Tags</span>
          <select multiple value={filters.tags} onChange={handleTagChange}>
            {availableTags.map((tag) => (
              <option key={tag.id} value={tag.name}>
                {tag.name}
              </option>
            ))}
          </select>
          <small className="muted">Cmd/Ctrl + click to select multiple.</small>
        </label>
        <label className="field">
          <span>Created from</span>
          <input type="date" name="createdFrom" value={filters.createdFrom} onChange={handleInputChange} />
        </label>
        <label className="field">
          <span>Created to</span>
          <input type="date" name="createdTo" value={filters.createdTo} onChange={handleInputChange} />
        </label>
      </div>
      <div className="filters-actions">
        <button type="button" className="ghost" onClick={onReset}>
          Reset
        </button>
      </div>
    </div>
  )
}
