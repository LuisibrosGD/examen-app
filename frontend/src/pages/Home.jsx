import { useEffect, useState } from 'react'
import { request } from '../api/client'
import { useAuth } from '../context/auth'

export default function Home() {
  const { user, logout } = useAuth()
  const [estado, setEstado] = useState('Conectando...')
  useEffect(() => {
    const controller = new AbortController()
    request('/health', { signal: controller.signal })
      .then((data) => setEstado(`API: ${data.status} | BD: ${data.database}`))
      .catch((error) => { if (!controller.signal.aborted) setEstado(`Error: ${error.message}`) })
    return () => controller.abort()
  }, [])
  return <>
    <p>Hola, {user.nombre} ({user.email}).</p>
    <h3>Estado de conexión</h3>
    <p role="status">{estado}</p>
    <button onClick={logout}>Cerrar sesión</button>
  </>
}
