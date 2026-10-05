import { useEffect, useState } from 'react'
import { request, tokenStore } from '../api/client'
import { AuthContext } from './auth'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(tokenStore.get)
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState(token ? 'loading' : 'anonymous')
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)

  function logout() {
    tokenStore.clear()
    setToken(null)
    setUser(null)
    setStatus('anonymous')
    setError('')
  }

  useEffect(() => {
    window.addEventListener('auth:expired', logout)
    return () => window.removeEventListener('auth:expired', logout)
  }, [])

  useEffect(() => {
    if (!token) return
    const controller = new AbortController()
    let expirationTimer
    request('/auth/me', { token, signal: controller.signal })
      .then((data) => {
        if (controller.signal.aborted) return
        setUser(data)
        setStatus('authenticated')
        // La autorización real la comprueba el servidor; esto actualiza la UI.
        const claims = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
        expirationTimer = setTimeout(logout, Math.max(0, Math.min(claims.exp * 1000 - Date.now(), 2147483647)))
      })
      .catch((err) => {
        if (controller.signal.aborted || tokenStore.get() !== token) return
        setError(err.message)
        setStatus('error')
      })
    return () => {
      controller.abort()
      clearTimeout(expirationTimer)
    }
  }, [token, retry])

  async function login(credentials) {
    const data = await request('/auth/login', { body: credentials })
    tokenStore.set(data.access_token)
    setUser(null)
    setError('')
    setStatus('loading')
    setToken(data.access_token)
    setRetry((value) => value + 1)
  }

  function retrySession() {
    setStatus('loading')
    setError('')
    setRetry((value) => value + 1)
  }

  return (
    <AuthContext.Provider value={{ user, token, status, error, login, logout, retrySession }}>
      {children}
    </AuthContext.Provider>
  )
}
