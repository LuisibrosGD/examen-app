import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL || "/api";

export default function App() {
  const [estado, setEstado] = useState("Conectando...");

  useEffect(() => {
    fetch(`${API}/health`)
      .then((r) => r.json())
      .then((d) => setEstado(`API: ${d.status} | BD: ${d.database}`))
      .catch((e) => setEstado(`Error: ${e.message}`));
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <h1>Examen App</h1>
      <h3>Estado de conexión</h3>
      <p>{estado}</p>
    </div>
  );
}
