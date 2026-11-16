// frontend/src/pages/Home.jsx
// Owner: Oussema
import React, { useEffect, useRef, useState } from 'react'
import Header from '../components/Header'
import Message from '../components/Message'
import SearchBar from '../components/SearchBar'
import Welcome from '../components/Welcome'
import { askCopilot, buildHistory, checkHealth, errorMessage } from '../lib/api'
import { MIN_QUESTION } from '../lib/constants'
import { mockResponse } from '../lib/mock'

const HEALTH_POLL_MS = 20000
let nextId = 1
const uid = () => nextId++

export default function Home() {
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('checking')      // checking | online | offline
  const [topK, setTopK] = useState(5)
  const [useGraph, setUseGraph] = useState(true)
  const endRef = useRef(null)

  // Poll /health (api/routes/health.py) so the header always shows the backend state
  useEffect(() => {
    let alive = true
    const poll = async () => {
      const ok = await checkHealth()
      if (alive) setStatus(ok ? 'online' : 'offline')
    }
    poll()
    const timer = setInterval(poll, HEALTH_POLL_MS)
    return () => { alive = false; clearInterval(timer) }
  }, [])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, loading])

  async function handleSend(raw, base = messages) {
    const question = raw.trim()
    if (question.length < MIN_QUESTION || loading) return

    const history = buildHistory(base)
    setMessages(m => [...m, { id: uid(), role: 'user', content: question }])
    setDraft('')
    setLoading(true)

    const started = performance.now()
    let data = null
    let demo = false
    try {
      if (status === 'offline') {
        demo = true
        await new Promise(r => setTimeout(r, 700))
        data = mockResponse(question)
      } else {
        data = await askCopilot({ question, topK, useGraph, history })
      }
    } catch (err) {
      if (!err.response) {                                // no answer at all: backend is down -> demo mode
        setStatus('offline')
        demo = true
        data = mockResponse(question)
      } else {
        setMessages(m => [...m, { id: uid(), role: 'error', content: errorMessage(err), question }])
      }
    }
    if (data) {
      setMessages(m => [...m, { id: uid(), role: 'assistant', data, demo, latency: performance.now() - started }])
    }
    setLoading(false)
  }

  function handleRetry(question) {
    // drop the failed exchange (question + error), then ask again
    const cut = messages.map(x => x.role === 'error' && x.question === question).lastIndexOf(true)
    const cleaned = cut < 0 ? messages : messages.filter((_, i) => i !== cut && i !== cut - 1)
    setMessages(cleaned)
    handleSend(question, cleaned)
  }

  return (
    <div className="app">
      <Header status={status} onReset={() => setMessages([])} canReset={messages.length > 0 && !loading} />

      <main className="thread">
        <div className="container">
          {messages.length === 0 && <Welcome onPick={setDraft} />}
          {messages.map(m => <Message key={m.id} message={m} onRetry={handleRetry} />)}
          {loading && (
            <div className="msg msg--assistant msg--loading" role="status" aria-live="polite">
              <span className="dots"><i /><i /><i /></span>
              Searching the documentation and the knowledge graph…
            </div>
          )}
          <div ref={endRef} />
        </div>
      </main>

      <footer className="composer">
        <div className="container">
          <SearchBar
            value={draft}
            onChange={setDraft}
            onSubmit={handleSend}
            disabled={loading}
            topK={topK}
            onTopK={setTopK}
            useGraph={useGraph}
            onUseGraph={setUseGraph}
          />
        </div>
      </footer>
    </div>
  )
}
