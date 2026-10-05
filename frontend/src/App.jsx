import { useEffect, useState } from 'react'
import './App.css'

const apiUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, '')

function App() {
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()

    async function checkHealth() {
      try {
        if (!apiUrl) throw new Error('Falta configurar VITE_API_URL.')
        const response = await fetch(`${apiUrl}/health`, {
          signal: controller.signal,
        })
        const data = await response.json()
        if (!response.ok) {
          throw new Error(data.detail || `Error HTTP ${response.status}`)
        }
        setResult(data)
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err.message || 'No se pudo conectar con el servidor.')
        }
      }
    }

    checkHealth()
    return () => controller.abort()
  }, [])

  return (
    <main className="health-card">
      <h1>Examen App</h1>
      <h2>Estado de conexión</h2>
      <div aria-live="polite">
        {!result && !error && <p>Comprobando conexión…</p>}
        {error && <p role="alert" className="error">{error}</p>}
        {result && (
          <>
            <p className="success">El backend y la base de datos están conectados.</p>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </>
        )}
      </div>
    </main>
  )
}

export default App
