import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="App">
      <header className="App-header">
        <h1>Plantilla React con Vite</h1>
        <p>
          Esta es una plantilla completa de React lista para usar en Roble
        </p>
        <div className="card">
          <button onClick={() => setCount((count) => count + 1)}>
            contador: {count}
          </button>
        </div>
        <div className="features">
          <h2>Características</h2>
          <ul>
            <li>⚡ Vite para desarrollo rápido</li>
            <li>⚛️ React 18</li>
            <li>🐳 Docker multi-stage build</li>
            <li>🚀 Optimizado para producción</li>
            <li>📦 Build estático con Nginx</li>
          </ul>
        </div>
      </header>
    </div>
  )
}

export default App
