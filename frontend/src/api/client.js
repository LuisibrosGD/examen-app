const API = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')
const TOKEN_KEY = 'examen.token'

export const tokenStore = {
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (token) => sessionStorage.setItem(TOKEN_KEY, token),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
}

export async function request(path, { token, body, signal } = {}) {
  const response = await fetch(`${API}${path}`, {
    method: body ? 'POST' : 'GET',
    headers: {
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
    signal,
  })
  const data = await response.json()
  if (!response.ok) {
    if (response.status === 401 && token === tokenStore.get()) {
      window.dispatchEvent(new Event('auth:expired'))
    }
    const message = Array.isArray(data.detail)
      ? data.detail.map((item) => `${item.loc.slice(1).join('.')}: ${item.msg}`).join('; ')
      : data.detail || `Error HTTP ${response.status}`
    throw new Error(message)
  }
  return data
}
