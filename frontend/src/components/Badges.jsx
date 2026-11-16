// frontend/src/components/Badges.jsx
// Owner: Oussema
// Small status elements shown above an answer: mode (intent), graph entities, reviewer verdict.
import React, { useState } from 'react'
import { INTENTS } from '../lib/constants'

export function IntentBadge({ intent }) {
  const f = INTENTS[intent]
  if (!f) return null
  return (
    <span className="badge badge--intent" title={f.hint}>
      <span className="badge__letter">{f.letter}</span>
      {f.title}
    </span>
  )
}

export function EntityChips({ entities }) {
  if (!entities || entities.length === 0) return null
  return (
    <span className="chips" aria-label="Concepts detected in the question">
      {entities.map(e => <span key={e} className="chip">{e}</span>)}
    </span>
  )
}

/** Verdict of agents/evaluation_assistant.review: grounded + cited, or a list of issues. */
export function ReviewBadge({ review }) {
  const [open, setOpen] = useState(false)
  if (!review) return null
  const issues = review.issues || []
  if (review.ok) {
    return <span className="badge badge--ok" title="Grounded in the sources and cited">✓ Verified</span>
  }
  return (
    <span className="review">
      <button type="button" className="badge badge--warn" onClick={() => setOpen(o => !o)} aria-expanded={open}>
        ! Needs checking ({issues.length})
      </button>
      {open && (
        <ul className="review__issues">
          {issues.map((issue, i) => <li key={i}>{issue}</li>)}
        </ul>
      )}
    </span>
  )
}
