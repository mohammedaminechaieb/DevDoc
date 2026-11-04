// frontend/src/components/SourcesList.jsx - Aya
import React from 'react'

export default function SourcesList({ sources }) {
  return (
    <div>
      <h3>Sources</h3>
      <ul>
        {sources.map((s, i) => (
          <li key={i}>
            <a href={s.url} target="_blank" rel="noreferrer">[{s.framework}] {s.url}</a>
          </li>
        ))}
      </ul>
    </div>
  )
}
