// frontend/src/components/SearchBar.jsx
// Owner: Oussema
// Question composer: auto-growing textarea (Enter sends, Shift+Enter = new line) and the search options.
import React, { useEffect, useRef } from 'react'
import { MAX_QUESTION, MIN_QUESTION, TOP_K_OPTIONS } from '../lib/constants'

export default function SearchBar({ value, onChange, onSubmit, disabled, topK, onTopK, useGraph, onUseGraph }) {
  const ref = useRef(null)
  const length = value.trim().length
  const canSend = !disabled && length >= MIN_QUESTION && value.length <= MAX_QUESTION

  useEffect(() => {                               // grow with the content, up to ~6 lines
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 150) + 'px'
  }, [value])

  function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (canSend) onSubmit(value)
    }
  }

  return (
    <form className="composer__form" onSubmit={e => { e.preventDefault(); if (canSend) onSubmit(value) }}>
      <div className="composer__box">
        <textarea
          ref={ref}
          rows={1}
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask about agents, LangGraph, CrewAI, MCP, or describe your project..."
          aria-label="Your question"
          maxLength={MAX_QUESTION}
        />
        <button type="submit" className="btn btn--primary" disabled={!canSend}>
          {disabled ? 'Thinking…' : 'Ask'}
        </button>
      </div>
      <div className="composer__options">
        <label className="option">
          Sources
          <select value={topK} onChange={e => onTopK(Number(e.target.value))} disabled={disabled}>
            {TOP_K_OPTIONS.map(k => <option key={k} value={k}>{k}</option>)}
          </select>
        </label>
        <label className="option option--toggle">
          <input type="checkbox" checked={useGraph} onChange={e => onUseGraph(e.target.checked)} disabled={disabled} />
          Knowledge graph
        </label>
        <span className="option__hint">Enter to send · Shift+Enter for a new line</span>
        {value.length > MAX_QUESTION * 0.9 && (
          <span className="option__hint option__hint--warn">{value.length}/{MAX_QUESTION}</span>
        )}
      </div>
    </form>
  )
}
