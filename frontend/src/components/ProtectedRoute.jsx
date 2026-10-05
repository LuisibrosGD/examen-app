import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/auth'

export default function ProtectedRoute() {
  const { status, error, logout, retrySession } = useAuth()
  const location = useLocation()
  if (status === 'loading') return <p role="status">Comprobando sesión…</p>
  if (status === 'error') {
    return <div><p role="alert">{error}</p><button onClick={retrySession}>Reintentar</button> <button onClick={logout}>Volver al login</button></div>
  }
  if (status !== 'authenticated') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  return <Outlet />
}
