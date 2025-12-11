const DEFAULT_ASSET_BASE = '/assets/'

function normalizeBase(base) {
  if (!base) {
    return DEFAULT_ASSET_BASE
  }
  return base.endsWith('/') ? base : `${base}/`
}

const ASSET_BASE_URL = normalizeBase(import.meta.env?.VITE_ASSET_BASE_URL || DEFAULT_ASSET_BASE)

export function buildAssetUrl(path) {
  if (!path) {
    return null
  }
  if (/^https?:/i.test(path)) {
    return path
  }
  const relative = path.startsWith('/') ? path.slice(1) : path
  return `${ASSET_BASE_URL}${relative}`
}

export function getAssetBase() {
  return ASSET_BASE_URL
}
