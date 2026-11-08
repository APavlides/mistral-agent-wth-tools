import { useEffect, useState } from 'react'

function App() {
  const [backend, setBackend] = useState('checking...')

  useEffect(() => {
    fetch('/api/health')
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then((data) => setBackend(data.status))
      .catch(() => setBackend('unreachable'))
  }, [])

  return (
    <main>
      <h1>Practice starter</h1>
      <p>Backend: {backend}</p>
    </main>
  )
}

export default App
