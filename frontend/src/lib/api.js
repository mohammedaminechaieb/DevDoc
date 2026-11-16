// frontend/src/lib/api.js
// Owner: Oussema
// All calls to the FastAPI backend (proxied by vite.config.js: /api and /health -> :8000).
import axios from 'axios'

const http = axios.create({ timeout: 180000 })   // local LLMs can be slow

/** GET /health (api/routes/health.py). Resolves true when the backend answers. */
export async function checkHealth() {
  try {
    const res = await http.get('/health', { timeout: 4000 })
    return res.data?.status === 'ok'
  } catch {
    return false
  }
}

/** POST /api/query -> {query, intent, entities, answer, sources, graph, review} */
export async function askCopilot({ question, topK, useGraph, history }) {
  const res = await http.post('/api/query', {
    question,
    top_k: topK,
    use_graph: useGraph,
    history,
  })
  return res.data
}

/** Human readable message for a failed request. */
export function errorMessage(err) {
  const status = err?.response?.status
  const detail = err?.response?.data?.detail
  if (status === 501) return 'The pipeline is not fully implemented yet: ' + (detail || 'a stage is missing.')
  if (status === 422) return 'The question was rejected: it must contain between 3 and 2000 characters.'
  if (status) return detail ? `Server error (${status}): ${detail}` : `Server error (${status}).`
  if (err?.code === 'ECONNABORTED') return 'The request took too long. Try again or lower the number of sources.'
  return 'Cannot reach the backend. Start it with: uvicorn api.main:app --reload'
}

/** Keeps the last turns for follow-up questions (the backend only reads the last few). */
export function buildHistory(messages, maxMessages = 8, maxChars = 1200) {
  return messages
    .filter(m => m.role === 'user' || (m.role === 'assistant' && m.data?.answer))
    .slice(-maxMessages)
    .map(m => ({
      role: m.role,
      content: (m.role === 'user' ? m.content : m.data.answer).slice(0, maxChars),
    }))
}
