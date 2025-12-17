import { useState } from 'react'

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
  const [dateHint, setDateHint] = useState('')

  const normalizeDateRange = (nextFilters) => {
    const { createdFrom, createdTo } = nextFilters
    if (createdFrom && createdTo) {
      const fromValue = new Date(createdFrom)
      const toValue = new Date(createdTo)
      if (!Number.isNaN(fromValue) && !Number.isNaN(toValue) && fromValue > toValue) {
        setDateHint('Adjusted dates so start comes before end.')
        return { ...nextFilters, createdFrom: createdTo, createdTo: createdFrom }
      }
    }
    setDateHint('')
    return nextFilters
  }

  const handleInputChange = (event) => {
    const { name, value } = event.target
    const nextFilters = normalizeDateRange({ ...filters, [name]: value })
    onFiltersChange(nextFilters)
  }

  const handleTagChange = (event) => {
    const selected = Array.from(event.target.selectedOptions).map((option) => option.value)
    const nextFilters = normalizeDateRange({ ...filters, tags: selected })
    onFiltersChange(nextFilters)
  }

  const handleReset = () => {
    setDateHint('')
    onReset()
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
          {dateHint ? <small className="muted">{dateHint}</small> : null}
        </label>
      </div>
      <div className="filters-actions">
        <button type="button" className="ghost" onClick={handleReset}>
          Reset
        </button>
      </div>
    </div>
  )
}
