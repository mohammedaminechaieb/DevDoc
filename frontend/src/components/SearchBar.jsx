// frontend/src/components/SearchBar.jsx - Aya
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
        placeholder="Ask about LangGraph, CrewAI, MCP..."
      />
      <button onClick={() => onSearch(input)} disabled={disabled}>Search</button>
    </div>
  )
}
