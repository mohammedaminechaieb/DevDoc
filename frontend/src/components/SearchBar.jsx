// frontend/src/components/SearchBar.jsx
// Owner: Aya
import React, { useState } from 'react'

export default function SearchBar({ onSearch, disabled }) {
  const [input, setInput] = useState('')
  return (
    <div>
      <input
        type="text"
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && !disabled && onSearch(input)}
        placeholder="Ask about agents, LangGraph, CrewAI, MCP, or describe your project..."
      />
      <button onClick={() => onSearch(input)} disabled={disabled}>Ask</button>
    </div>
  )
}
