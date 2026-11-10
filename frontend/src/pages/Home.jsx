// frontend/src/pages/Home.jsx
// Owner: Oussema
import React, { useState } from 'react'
import SearchBar from '../components/SearchBar'
import AnswerCard from '../components/AnswerCard'
import SourcesList from '../components/SourcesList'
import GraphViewer from '../components/GraphViewer'
import axios from 'axios'

// Mock response - used while the backend is not ready
const MOCK = {
  query: 'What is LangGraph?',
  intent: 'learn',
  answer: 'LangGraph is a library for building stateful, multi-actor applications with LLMs.',
  sources: [{ chunk_id: 'mock', url: 'https://langchain-ai.github.io/langgraph/', framework: 'langgraph', text: '...' }],
  graph: { nodes: [], edges: [] }
}

export default function Home() {
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [healthy, setHealthy] = useState(null)

  // Poll /health before enabling search (served by api/routes/health.py)
  React.useEffect(() => {
    axios.get('/health')
      .then(() => setHealthy(true))
      .catch(() => setHealthy(false))
  }, [])

  async function handleSearch(question) {
    if (!question.trim()) return
    setLoading(true)
    let data
    try {
      const res = await axios.post('/api/query', { question, top_k: 5, use_graph: true, history })
      data = res.data
    } catch {
      // Fall back to mock while backend is under development
      data = { ...MOCK, query: question }
    }
    setResult(data)
    setHistory(h => [...h, { role: 'user', content: question }, { role: 'assistant', content: data.answer }])
    setLoading(false)
  }

  return (
    <div>
      <h1>Agentic AI Copilot</h1>
      {healthy === false && <p style={{ color: 'red' }}>Backend offline - using mock data</p>}
      <SearchBar onSearch={handleSearch} disabled={loading} />
      {loading && <p>Thinking...</p>}
      {result && result.intent && <p><small>Mode: {result.intent}</small></p>}
      {result && <AnswerCard answer={result.answer} />}
      {result && <SourcesList sources={result.sources} />}
      {result && <GraphViewer data={result.graph} />}
    </div>
  )
}
