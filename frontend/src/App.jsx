import { BrowserRouter, Navigate, NavLink, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import { SettingsProvider, useSettings } from './context/SettingsContext'
import LoginPage from './pages/LoginPage'
import ItemsPage from './pages/ItemsPage'
import ItemDetailPage from './pages/ItemDetailPage'
import InfoPage from './pages/InfoPage'

function RequireAuth() {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}

function AppLayout() {
  const { logout } = useAuth()
  const { settings } = useSettings()
  const location = useLocation()
  const [navOpen, setNavOpen] = useState(false)
  const themeClass = `theme-editorial theme-${settings.themeIntensity} motion-${settings.motion}`

  useEffect(() => {
    setNavOpen(false)
  }, [location.pathname])

  return (
    <div className={`app-shell ${themeClass} ${navOpen ? 'nav-open' : ''}`}>
      <header className="app-header">
        <div className="brand wordmark">
          <span className="brand-dot" />
          <div className="brand-text">
            <span className="brand-eyebrow">BRAIN</span>
            <span className="brand-mark">Editorial Portfolio</span>
          </div>
        </div>
        <button
          type="button"
          className="nav-toggle"
          aria-label="Toggle navigation"
          aria-expanded={navOpen}
          onClick={() => setNavOpen((open) => !open)}
        >
          <span />
          <span />
        </button>
        <nav className={`app-nav ${navOpen ? 'open' : ''}`}>
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Board
          </NavLink>
          <NavLink to="/info" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Info
          </NavLink>
          <button type="button" className="nav-link ghost" onClick={logout}>
            Log out
          </button>
        </nav>
      </header>
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <SettingsProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<RequireAuth />}>
              <Route element={<AppLayout />}>
                <Route path="/" element={<ItemsPage />} />
                <Route path="/items/:itemId" element={<ItemDetailPage />} />
                <Route path="/info" element={<InfoPage />} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </SettingsProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
