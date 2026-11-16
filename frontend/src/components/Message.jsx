// frontend/src/components/Message.jsx
// Owner: Oussema
// One entry of the conversation: the user's question, the copilot's answer, or an error.
import React, { Suspense, lazy, useState } from 'react'
import AnswerCard from './AnswerCard'
import SourcesList from './SourcesList'
import { EntityChips, IntentBadge, ReviewBadge } from './Badges'

// the graph library is heavy and the graph tab is not the default one: load it on demand
const GraphViewer = lazy(() => import('./GraphViewer'))

function AssistantMessage({ message }) {
  const { data, latency, demo } = message
  const sources = data.sources || []
  const nodes = data.graph?.nodes?.length || 0
  const [tab, setTab] = useState('sources')
  const [highlight, setHighlight] = useState(null)

  function openSource(n) {
    setTab('sources')
    setHighlight({ n, at: Date.now() })           // new object each click, so the effect re-runs
  }

  return (
    <div className="msg msg--assistant">
      <div className="meta">
        <IntentBadge intent={data.intent} />
        <EntityChips entities={data.entities} />
        <ReviewBadge review={data.review} />
        {demo && <span className="badge badge--demo">Demo answer</span>}
        {latency != null && <span className="meta__time">{(latency / 1000).toFixed(1)} s</span>}
      </div>

      <AnswerCard answer={data.answer} onCite={openSource} />

      <div className="tabs" role="tablist">
        <button type="button" role="tab" aria-selected={tab === 'sources'}
                className={`tab ${tab === 'sources' ? 'tab--active' : ''}`} onClick={() => setTab('sources')}>
          Sources <span className="tab__count">{sources.length}</span>
        </button>
        <button type="button" role="tab" aria-selected={tab === 'graph'}
                className={`tab ${tab === 'graph' ? 'tab--active' : ''}`} onClick={() => setTab('graph')}>
          Knowledge graph <span className="tab__count">{nodes}</span>
        </button>
      </div>
      <div className="tabpanel">
        {tab === 'sources'
          ? <SourcesList sources={sources} highlight={highlight} />
          : (
            <Suspense fallback={<p className="empty">Loading the graph…</p>}>
              <GraphViewer data={data.graph} />
            </Suspense>
          )}
      </div>
    </div>
  )
}

export default function Message({ message, onRetry }) {
  if (message.role === 'user') {
    return <div className="msg msg--user"><p>{message.content}</p></div>
  }
  if (message.role === 'error') {
    return (
      <div className="msg msg--error" role="alert">
        <strong>Something went wrong</strong>
        <p>{message.content}</p>
        {message.question && (
          <button type="button" className="btn btn--outline" onClick={() => onRetry(message.question)}>Try again</button>
        )}
      </div>
    )
  }
  return <AssistantMessage message={message} />
}
