// frontend/src/components/SourcesList.jsx
// Owner: Oussema
// Numbered like the context blocks of generation/prompt_builder.py, so [n] in the answer = source n.
import React, { useEffect, useState } from 'react'

const SNIPPET = 260

/** The corpus stores file:// paths; real web pages are shown as host + path. */
function displayName(url) {
  if (!url) return 'unknown source'
  if (url.startsWith('file://')) return url.replace(/^file:\/\/(raw_docs\/)?/, '')
  try {
    const u = new URL(url)
    return (u.host + u.pathname).replace(/\/$/, '')
  } catch {
    return url
  }
}

function Source({ index, source, active }) {
  const [expanded, setExpanded] = useState(false)
  const text = (source.text || '').trim()
  const long = text.length > SNIPPET
  const isWeb = /^https?:\/\//.test(source.url || '')

  return (
    <li id={`source-${index}`} className={`source ${active ? 'source--active' : ''}`}>
      <span className="source__num">{index}</span>
      <div className="source__body">
        <div className="source__head">
          <span className="pill">{source.framework || 'unknown'}</span>
          {isWeb
            ? <a href={source.url} target="_blank" rel="noreferrer" className="source__link">{displayName(source.url)}</a>
            : <span className="source__link source__link--plain">{displayName(source.url)}</span>}
        </div>
        {text && (
          <p className="source__text">
            {expanded || !long ? text : text.slice(0, SNIPPET).trimEnd() + '…'}
            {long && (
              <button type="button" className="linklike" onClick={() => setExpanded(e => !e)}>
                {expanded ? 'Show less' : 'Show more'}
              </button>
            )}
          </p>
        )}
      </div>
    </li>
  )
}

export default function SourcesList({ sources, highlight }) {
  const [active, setActive] = useState(null)

  useEffect(() => {                               // a citation [n] was clicked in the answer
    if (!highlight) return
    setActive(highlight.n)
    document.getElementById(`source-${highlight.n}`)?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    const t = setTimeout(() => setActive(null), 2200)
    return () => clearTimeout(t)
  }, [highlight])

  if (!sources || sources.length === 0) {
    return <p className="empty">No source was used for this answer.</p>
  }
  return (
    <ol className="sources">
      {sources.map((s, i) => <Source key={s.chunk_id || i} index={i + 1} source={s} active={active === i + 1} />)}
    </ol>
  )
}
