// frontend/src/components/Welcome.jsx
// Owner: Oussema
// Empty state: the six features of NLP.pdf section 4, each with a ready-to-send example.
import React from 'react'
import { EXAMPLES, INTENTS } from '../lib/constants'

export default function Welcome({ onPick }) {
  return (
    <section className="welcome">
      <h2 className="welcome__title">What are you building today?</h2>
      <p className="welcome__lead">
        Ask about agents, LangGraph, CrewAI, AutoGen or MCP. Answers are grounded in the official
        documentation and enriched with a knowledge graph.
      </p>
      <div className="feature-grid">
        {Object.entries(INTENTS).map(([key, f]) => (
          <button key={key} type="button" className="feature" onClick={() => onPick(EXAMPLES[key])}>
            <span className="feature__letter">{f.letter}</span>
            <span className="feature__title">{f.title}</span>
            <span className="feature__hint">{f.hint}</span>
            <span className="feature__example">“{EXAMPLES[key]}”</span>
          </button>
        ))}
      </div>
    </section>
  )
}
