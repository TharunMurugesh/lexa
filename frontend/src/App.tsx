import { useEffect, useState } from 'react'

function App() {
  const [status, setStatus] = useState<string>('Checking...')

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then((res) => res.json())
      .then((data) => setStatus(data.status))
      .catch((err) => setStatus('Error: ' + err.message))
  }, [])

  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-800 rounded-xl shadow-2xl p-8 border border-slate-700">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent mb-6 text-center">
          LEXA
        </h1>
        <p className="text-slate-300 text-center mb-8">
          Multi-Agent Legal Reasoning System
        </p>
        
        <div className="bg-slate-900/50 rounded-lg p-4 flex items-center justify-between border border-slate-700/50">
          <span className="text-sm font-medium text-slate-400">API Status</span>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${status === 'ok' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`}></div>
            <span className="text-sm font-mono text-slate-300">{status}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
