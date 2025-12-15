import { clearToken, loadStoredToken } from './session'

const DEFAULT_BASE_URL = '/api'
const API_BASE_URL = normalizeBase(import.meta.env?.VITE_API_BASE_URL || DEFAULT_BASE_URL)

function normalizeBase(base) {
  if (!base) {
    return DEFAULT_BASE_URL
  }
  if (base.endsWith('/')) {
    return base.slice(0, -1)
  }
  return base
}

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

function buildQuery(params) {
  if (!params) {
    return ''
  }
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return
    }
    if (Array.isArray(value)) {
      value.forEach((entry) => {
        if (entry !== undefined && entry !== null && entry !== '') {
          query.append(key, entry)
        }
      })
      return
    }
    query.append(key, value)
  })
  const serialized = query.toString()
  return serialized ? `?${serialized}` : ''
}

export async function request(
  path,
  { method = 'GET', body, headers = {}, params, skipAuth = false, signal } = {}
) {
  const url = `${API_BASE_URL}${path}${buildQuery(params)}`
  const requestInit = {
    method,
    headers: {
      Accept: 'application/json',
      ...headers,
    },
  }

  if (signal) {
    requestInit.signal = signal
  }

  const token = !skipAuth ? loadStoredToken() : null
  if (token) {
    requestInit.headers.Authorization = `Bearer ${token}`
  }

  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData
  if (body !== undefined) {
    if (isFormData) {
      requestInit.body = body
    } else {
      requestInit.headers['Content-Type'] = 'application/json'
      requestInit.body = typeof body === 'string' ? body : JSON.stringify(body)
    }
  }

  const response = await fetch(url, requestInit)
  const contentType = response.headers.get('content-type') || ''
  const hasBody = response.status !== 204 && response.headers.get('content-length') !== '0'
  const isJson = contentType.includes('application/json')
  let payload = null

  if (hasBody) {
    try {
      payload = isJson ? await response.json() : await response.text()
    } catch (err) {
      // Gracefully handle empty/invalid JSON responses.
      if (isJson) {
        payload = null
      } else {
        throw err
      }
    }
  }

  if (!response.ok) {
    if (response.status === 401 && !skipAuth && token) {
      clearToken()
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('brain:auth:unauthorized'))
      }
    }
    const message = isJson
      ? payload?.detail || 'Request failed'
      : typeof payload === 'string' && payload
        ? payload
        : 'Request failed'
    throw new ApiError(message, response.status, payload)
  }

  return payload
}

export const api = {
  login(credentials) {
    return request('/auth/login', {
      method: 'POST',
      body: credentials,
      skipAuth: true,
    })
  },
  getItems(params, options) {
    return request('/items/', {
      method: 'GET',
      params,
      ...options,
    })
  },
  getItem(id) {
    return request(`/items/${id}`)
  },
  createItemFromUrl(payload) {
    return request('/items/url', {
      method: 'POST',
      body: payload,
    })
  },
  uploadItem(payload) {
    return request('/items/upload', {
      method: 'POST',
      body: payload,
    })
  },
  updateItem(id, payload) {
    return request(`/items/${id}`, {
      method: 'PATCH',
      body: payload,
    })
  },
  replaceItemTags(id, tags) {
    return request(`/items/${id}/tags`, {
      method: 'PUT',
      body: { tags },
    })
  },
  deleteItem(id) {
    return request(`/items/${id}`, {
      method: 'DELETE',
    })
  },
  getTags(options) {
    return request('/tags/', {
      method: 'GET',
      ...options,
    })
  },
}
