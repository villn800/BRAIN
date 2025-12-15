import { createPortal } from 'react-dom'
import { useSettings } from '../context/SettingsContext'
import { useEffect, useRef } from 'react'

export default function SettingsModal({ open, onClose }) {
  const { settings, setSetting, resetSettings } = useSettings()
  const dialogRef = useRef(null)
  const themeIntensityOptions =
    settings.themeStyle === 'twitter'
      ? [
          { value: 'soft', label: 'Dim', hint: 'Twitter dim dark' },
          { value: 'bold', label: 'Lights out', hint: 'Pure black background' },
        ]
      : [
          { value: 'soft', label: 'Soft', hint: 'Light gradient, airy cards, gentle borders' },
          { value: 'bold', label: 'Bold', hint: 'Richer gradient, stronger contrast & accent' },
        ]

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

  useEffect(() => {
    if (!open) {
      return undefined
    }
    const node = dialogRef.current
    const closeOnEsc = (event) => {
      if (event.key === 'Escape') {
        onClose?.()
      }
      if (event.key !== 'Tab' || !node) {
        return
      }
      const focusable = node.querySelectorAll(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
      )
      const entries = Array.from(focusable)
      if (!entries.length) {
        return
      }
      const first = entries[0]
      const last = entries[entries.length - 1]
      if (event.shiftKey) {
        if (document.activeElement === first) {
          event.preventDefault()
          last.focus()
        }
      } else if (document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    window.addEventListener('keydown', closeOnEsc)
    const firstFocusable = node?.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
    firstFocusable?.focus()
    return () => window.removeEventListener('keydown', closeOnEsc)
  }, [open, onClose])

  if (!open) {
    return null
  }

  return createPortal(
    <div className="detail-overlay settings-overlay" onClick={onClose}>
      <div
        className="settings-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Board settings"
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
        ref={dialogRef}
      >
        <header className="settings-header">
          <div>
            <p className="eyebrow">Board settings</p>
            <h2>Personalize your board</h2>
            <p className="muted">Density, media sizing, overlays, theme, and motion are saved to this browser.</p>
          </div>
          <button type="button" className="ghost" onClick={onClose}>
            Close ✕
          </button>
        </header>

        <div className="settings-body">
          <div className="settings-columns">
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
          </div>

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

          <fieldset className="settings-group">
            <legend>Theme</legend>
            <div className="settings-options">
              {[
                { value: 'editorial', label: 'Editorial', hint: 'Warm editorial surfaces' },
                { value: 'twitter', label: 'Twitter', hint: 'Twitter/X dark mode palette' },
              ].map((entry) => (
                <label key={entry.value} className="option-tile">
                  <input
                    type="radio"
                    name="themeStyle"
                    value={entry.value}
                    checked={settings.themeStyle === entry.value}
                    onChange={(event) => setSetting('themeStyle', event.target.value)}
                  />
                  <span className="option-title">{entry.label}</span>
                  <span className="option-hint">{entry.hint}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="settings-group">
            <legend>Theme intensity</legend>
            <div className="settings-options">
              {themeIntensityOptions.map((entry) => (
                <label key={entry.value} className="option-tile">
                  <input
                    type="radio"
                    name="themeIntensity"
                    value={entry.value}
                    checked={settings.themeIntensity === entry.value}
                    onChange={(event) => setSetting('themeIntensity', event.target.value)}
                  />
                  <span className="option-title">{entry.label}</span>
                  <span className="option-hint">{entry.hint}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="settings-group">
            <legend>Motion</legend>
            <div className="settings-options">
              {[
                { value: 'standard', label: 'Standard', hint: 'Hover lift + smooth transitions' },
                { value: 'reduced', label: 'Reduced', hint: 'Minimal motion; respects system prefs' },
              ].map((entry) => (
                <label key={entry.value} className="option-tile">
                  <input
                    type="radio"
                    name="motion"
                    value={entry.value}
                    checked={settings.motion === entry.value}
                    onChange={(event) => setSetting('motion', event.target.value)}
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
