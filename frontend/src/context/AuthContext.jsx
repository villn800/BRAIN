import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import { clearToken, loadStoredToken, persistToken } from '../lib/session'

const AuthContext = createContext(undefined)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => loadStoredToken())
  const [authLoading, setAuthLoading] = useState(false)
  const [authError, setAuthError] = useState(null)
  const [isReady, setIsReady] = useState(false)
  const [authNotice, setAuthNotice] = useState(null)

  useEffect(() => {
    setIsReady(true)
  }, [])

  useEffect(() => {
    const handleUnauthorized = () => {
      setToken(null)
      setAuthError(null)
      setAuthNotice('Session expired. Please log in again.')
    }

    window.addEventListener('brain:auth:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('brain:auth:unauthorized', handleUnauthorized)
  }, [])

  useEffect(() => {
    if (token) {
      persistToken(token)
    } else {
      clearToken()
    }
  }, [token])

  const login = useCallback(async ({ identifier, password }) => {
    setAuthLoading(true)
    setAuthError(null)
    try {
      const response = await api.login({ identifier, password })
      persistToken(response.access_token)
      setAuthNotice(null)
      setToken(response.access_token)
      return response
    } catch (error) {
      setAuthError(error)
      throw error
    } finally {
      setAuthLoading(false)
    }
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setAuthError(null)
    setAuthNotice(null)
  }, [])

  const clearAuthNotice = useCallback(() => {
    setAuthNotice(null)
  }, [])

  const value = useMemo(
    () => ({
      token,
      isAuthenticated: Boolean(token),
      isReady,
      authLoading,
      authError,
      authNotice,
      login,
      logout,
      clearAuthNotice,
    }),
    [token, isReady, authLoading, authError, authNotice, login, logout, clearAuthNotice]
  )

  if (!isReady) {
    return null
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
