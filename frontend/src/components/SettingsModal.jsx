import { createPortal } from 'react-dom'
import { useSettings } from '../context/SettingsContext'
import { useEffect } from 'react'

export default function SettingsModal({ open, onClose }) {
  const { settings, setSetting, resetSettings } = useSettings()

  if (!open) {
    return null
  }

  useEffect(() => {
    if (!open) {
      return undefined
    }
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = previousOverflow
    }
  }, [open])

  return createPortal(
    <div className="detail-overlay settings-overlay" onClick={onClose}>
      <div className="settings-modal" role="dialog" aria-modal="true" aria-label="Board settings" onClick={(e) => e.stopPropagation()}>
        <header className="settings-header">
          <div>
            <p className="eyebrow">Board settings</p>
            <h2>Personalize your view</h2>
            <p className="muted">Density, thumbnail size, and hover behavior are saved to this browser.</p>
          </div>
          <button type="button" className="ghost" onClick={onClose}>
            Close ✕
          </button>
        </header>

        <div className="settings-body">
          <fieldset className="settings-group">
            <legend>Grid density</legend>
            <div className="settings-options">
              {['compact', 'cozy', 'airy'].map((value) => (
                <label key={value} className="option-tile">
                  <input
                    type="radio"
                    name="gridDensity"
                    value={value}
                    checked={settings.gridDensity === value}
                    onChange={(event) => setSetting('gridDensity', event.target.value)}
                  />
                  <span className="option-title">{value}</span>
                  <span className="option-hint">
                    {value === 'compact'
                      ? 'Tight packing'
                      : value === 'cozy'
                        ? 'Balanced'
                        : 'Extra breathing room'}
                  </span>
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="settings-group">
            <legend>Thumbnail height</legend>
            <div className="settings-options">
              {['small', 'medium', 'large'].map((value) => (
                <label key={value} className="option-tile">
                  <input
                    type="radio"
                    name="thumbSize"
                    value={value}
                    checked={settings.thumbSize === value}
                    onChange={(event) => setSetting('thumbSize', event.target.value)}
                  />
                  <span className="option-title">{value}</span>
                  <span className="option-hint">
                    {value === 'small' ? 'Snappier scroll' : value === 'medium' ? 'Default' : 'Big visuals'}
                  </span>
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="settings-group">
            <legend>Metadata display</legend>
            <div className="settings-options">
              {[
                { value: 'hover', label: 'On hover', hint: 'Reveal overlay when exploring' },
                { value: 'always', label: 'Always on', hint: 'Keep overlay visible for quick scanning' },
              ].map((entry) => (
                <label key={entry.value} className="option-tile">
                  <input
                    type="radio"
                    name="overlayMode"
                    value={entry.value}
                    checked={settings.overlayMode === entry.value}
                    onChange={(event) => setSetting('overlayMode', event.target.value)}
                  />
                  <span className="option-title">{entry.label}</span>
                  <span className="option-hint">{entry.hint}</span>
                </label>
              ))}
            </div>
          </fieldset>
        </div>

        <footer className="settings-footer">
          <button type="button" className="ghost" onClick={() => resetSettings()}>
            Reset to defaults
          </button>
          <button type="button" onClick={onClose}>
            Done
          </button>
        </footer>
      </div>
    </div>,
    document.body
  )
}
