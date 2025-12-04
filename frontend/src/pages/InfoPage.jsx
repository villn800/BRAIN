import { useEffect, useMemo } from 'react'
import { useSettings } from '../context/SettingsContext'

export default function InfoPage() {
  const { settings } = useSettings()
  const headline = useMemo(
    () =>
      settings.themeIntensity === 'bold'
        ? 'Portfolio notes & workflow'
        : 'Notes from the studio portfolio',
    [settings.themeIntensity]
  )

  useEffect(() => {
    document.title = 'BRAIN — Info'
  }, [])

  return (
    <div className="info-page">
      <div className="info-hero">
        <p className="eyebrow">Info</p>
        <h1>{headline}</h1>
        <p className="muted">
          BRAIN is a photographer-inspired vault: the board stays live on the right, and this page hosts the
          story—purpose, process, and how to navigate the editorial shell.
        </p>
      </div>

      <section className="info-section">
        <div>
          <h3>What lives here</h3>
          <p>
            The board is the hero surface. Save links, upload shots, and scan tags; each tile opens into a story-like
            detail view. Settings tune density, thumb scale, overlays, and motion to fit your screen and taste.
          </p>
        </div>
        <div className="info-grid">
          <div className="info-card">
            <p className="eyebrow">Board</p>
            <h4>Editorial masonry</h4>
            <p className="muted">
              Minimal chrome, generous imagery, and overlays that carry the title plus a single meta line.
            </p>
          </div>
          <div className="info-card">
            <p className="eyebrow">Tools</p>
            <h4>Filters & ingest</h4>
            <p className="muted">
              Search by keyword, type, tag, or date; paste a URL or upload an asset without leaving the spread.
            </p>
          </div>
          <div className="info-card">
            <p className="eyebrow">Detail</p>
            <h4>Story layout</h4>
            <p className="muted">
              Hero image first, then tidy metadata and tags. “Full view” keeps a deep link to the item.
            </p>
          </div>
        </div>
      </section>

      <section className="info-section">
        <div>
          <h3>How to use it</h3>
          <ul className="info-list">
            <li>Start on the Board route; it is the home.</li>
            <li>Use the Tools rail to filter, paste links, or upload imagery.</li>
            <li>Hover for quick metadata; click to open the story panel.</li>
            <li>Board Settings live in the header—tune density, motion, and overlays.</li>
          </ul>
        </div>
        <div className="info-note">
          <p className="eyebrow">Editorial palette</p>
          <p>
            Warm charcoal, paper textures, and a copper accent borrowed from Mark Clennon’s portfolio sensibility. Fonts
            pair a serif display with a clean sans for body and navigation.
          </p>
        </div>
      </section>
    </div>
  )
}
