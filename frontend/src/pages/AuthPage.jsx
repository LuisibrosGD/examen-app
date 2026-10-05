import { useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { request } from '../api/client'
import { useAuth } from '../context/auth'

export default function AuthPage({ register = false }) {
  const { login, status, error: sessionError, retrySession, logout } = useAuth()
  const location = useLocation()
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  if (status === 'authenticated') return <Navigate to={location.state?.from || '/'} replace />

  async function submit(event) {
    event.preventDefault()
    const form = event.currentTarget
    const data = Object.fromEntries(new FormData(form))
    setError('')
    setMessage('')
    setBusy(true)
    try {
      if (register) {
        await request('/auth/registro', { body: data })
        form.reset()
        setMessage('Cuenta creada. Ya puedes iniciar sesión.')
      } else {
        await login(data)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <h3>{register ? 'Crear cuenta' : 'Iniciar sesión'}</h3>
      <form onSubmit={submit}>
        <fieldset disabled={busy || status === 'loading'} style={{ border: 0, padding: 0 }}>
          {register && <p><label>Nombre<br /><input name="nombre" autoComplete="name" required maxLength={150} /></label></p>}
          <p><label>Email<br /><input name="email" type="email" autoComplete="email" required maxLength={254} /></label></p>
          <p><label>Contraseña<br /><input name="password" type="password" autoComplete={register ? 'new-password' : 'current-password'} required minLength={register ? 8 : 1} maxLength={128} /></label></p>
          <button type="submit">{busy ? 'Enviando…' : register ? 'Registrarme' : 'Entrar'}</button>
        </fieldset>
      </form>
      {status === 'loading' && <p role="status">Comprobando sesión…</p>}
      {status === 'error' && <div><p role="alert">{sessionError}</p><button onClick={retrySession}>Reintentar sesión</button> <button onClick={logout}>Cancelar sesión</button></div>}
      {error && <p role="alert">{error}</p>}
      {message && <p role="status">{message}</p>}
      <p><Link to={register ? '/login' : '/registro'}>{register ? 'Ir al login' : 'Crear cuenta'}</Link></p>
    </>
  )
}
