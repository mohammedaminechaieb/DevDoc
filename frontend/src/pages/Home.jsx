// frontend/src/pages/Home.jsx - Aya
import React, { useState } from 'react'
import SearchBar from '../components/SearchBar'
import AnswerCard from '../components/AnswerCard'
import SourcesList from '../components/SourcesList'
import axios from 'axios'

// Mock response - use this while backend is not ready
const MOCK = {
  answer: "LangGraph is a library for building stateful, multi-actor applications with LLMs.",
  sources: [{ url: "https://docs.langchain.com/langgraph/overview", framework: "langgraph", text: "..." }],
  query: "What is LangGraph?"
}

export default function Home() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [healthy, setHealthy] = useState(null)

  // Poll /health before enabling search (Aya owns /health too)
  React.useEffect(() => {
    axios.get('/health')
      .then(() => setHealthy(true))
      .catch(() => setHealthy(false))
  }, [])

  async function handleSearch(question) {
    setLoading(true)
    try {
      const res = await axios.post('/api/query', { question, top_k: 5, use_graph: true })
      setResult(res.data)
    } catch {
      // Fall back to mock while backend is under development
      setResult({ ...MOCK, query: question })
    }
    setLoading(false)
  }

  return (
    <div>
      <h1>DevDoc AI</h1>
      {healthy === false && <p style={{color:'red'}}>Backend offline - using mock data</p>}
      <SearchBar onSearch={handleSearch} disabled={loading} />
      {loading && <p>Loading...</p>}
      {result && <AnswerCard answer={result.answer} />}
      {result && <SourcesList sources={result.sources} />}
    </div>
  )
}
