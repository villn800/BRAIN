import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const STORAGE_KEY = 'brain-ui-settings'
const DEFAULT_SETTINGS = {
  gridDensity: 'cozy',
  thumbSize: 'medium',
  overlayMode: 'hover',
}

const SettingsContext = createContext({
  settings: DEFAULT_SETTINGS,
  setSetting: () => {},
  resetSettings: () => {},
})

function loadStoredSettings() {
  if (typeof localStorage === 'undefined') {
    return null
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return null
    }
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') {
      return null
    }
    return {
      gridDensity: parsed.gridDensity || DEFAULT_SETTINGS.gridDensity,
      thumbSize: parsed.thumbSize || DEFAULT_SETTINGS.thumbSize,
      overlayMode: parsed.overlayMode || DEFAULT_SETTINGS.overlayMode,
    }
  } catch {
    return null
  }
}

export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState(() => loadStoredSettings() || DEFAULT_SETTINGS)

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
    } catch {
      /* ignore storage write errors */
    }
  }, [settings])

  const setSetting = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  const resetSettings = () => setSettings(DEFAULT_SETTINGS)

  const value = useMemo(
    () => ({
      settings,
      setSetting,
      resetSettings,
      defaults: DEFAULT_SETTINGS,
    }),
    [settings]
  )

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
}

export function useSettings() {
  return useContext(SettingsContext)
}
