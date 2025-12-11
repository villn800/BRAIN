const TOKEN_STORAGE_KEY = 'brain.auth.token'

function getStorage() {
  if (typeof window === 'undefined') {
    return null
  }
  try {
    return window.localStorage
  } catch {
    return null
  }
}

export function loadStoredToken() {
  const storage = getStorage()
  if (!storage) {
    return null
  }
  try {
    return storage.getItem(TOKEN_STORAGE_KEY)
  } catch {
    return null
  }
}

export function persistToken(token) {
  const storage = getStorage()
  if (!storage) {
    return
  }
  try {
    storage.setItem(TOKEN_STORAGE_KEY, token)
  } catch {
    /* ignore write failures */
  }
}

export function clearToken() {
  const storage = getStorage()
  if (!storage) {
    return
  }
  try {
    storage.removeItem(TOKEN_STORAGE_KEY)
  } catch {
    /* ignore clear failures */
  }
}
