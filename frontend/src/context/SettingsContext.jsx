import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const STORAGE_KEY = 'brain-ui-settings'
const ALLOWED_VALUES = {
  gridDensity: ['compact', 'cozy', 'airy'],
  thumbSize: ['small', 'medium', 'large'],
  overlayMode: ['hover', 'always'],
  themeIntensity: ['soft', 'bold'],
  motion: ['standard', 'reduced'],
}

const BASE_DEFAULTS = {
  gridDensity: 'cozy',
  thumbSize: 'medium',
  overlayMode: 'hover',
  themeIntensity: 'soft',
  motion: 'standard',
}

function getDefaultSettings() {
  const prefersReduced =
    typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  return {
    ...BASE_DEFAULTS,
    motion: prefersReduced ? 'reduced' : BASE_DEFAULTS.motion,
  }
}

const SettingsContext = createContext({
  settings: BASE_DEFAULTS,
  setSetting: () => {},
  resetSettings: () => {},
})

function loadStoredSettings() {
  if (typeof localStorage === 'undefined') {
    return null
  }
  const defaults = getDefaultSettings()
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return null
    }
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') {
      return null
    }
    return normalizeSettings(parsed, defaults)
  } catch {
    return null
  }
}

export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState(() => loadStoredSettings() || getDefaultSettings())

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
    } catch {
      /* ignore storage write errors */
    }
  }, [settings])

  const setSetting = (key, value) => {
    if (!ALLOWED_VALUES[key] || !ALLOWED_VALUES[key].includes(value)) {
      return
    }
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  const resetSettings = () => setSettings(getDefaultSettings())

  const value = useMemo(
    () => ({
      settings,
      setSetting,
      resetSettings,
      defaults: getDefaultSettings(),
    }),
    [settings]
  )

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
}

export function useSettings() {
  return useContext(SettingsContext)
}

function normalizeSettings(candidate, defaults) {
  const next = { ...defaults }
  Object.entries(ALLOWED_VALUES).forEach(([key, allowed]) => {
    if (allowed.includes(candidate[key])) {
      next[key] = candidate[key]
    }
  })
  return next
}
