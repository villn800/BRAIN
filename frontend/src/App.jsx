import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { SettingsProvider, useSettings } from './context/SettingsContext'
import LoginPage from './pages/LoginPage'
import ItemsPage from './pages/ItemsPage'
import ItemDetailPage from './pages/ItemDetailPage'

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
  const themeClass = `theme-${settings.themeIntensity} motion-${settings.motion}`

  return (
    <div className={`app-shell ${themeClass}`}>
      <header className="app-header">
        <div className="brand">
          <span className="brand-dot" />
          <span>BRAIN Inspiration Vault</span>
        </div>
        <button type="button" className="ghost" onClick={logout}>
          Log out
        </button>
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
