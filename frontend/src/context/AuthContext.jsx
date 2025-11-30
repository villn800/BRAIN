import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import { clearToken, loadStoredToken, persistToken } from '../lib/session'

const AuthContext = createContext(undefined)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => loadStoredToken())
  const [authLoading, setAuthLoading] = useState(false)
  const [authError, setAuthError] = useState(null)
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    setIsReady(true)
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
  }, [])

  const value = useMemo(
    () => ({
      token,
      isAuthenticated: Boolean(token),
      isReady,
      authLoading,
      authError,
      login,
      logout,
    }),
    [token, isReady, authLoading, authError, login, logout]
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
