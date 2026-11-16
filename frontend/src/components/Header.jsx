// frontend/src/components/Header.jsx
// Owner: Oussema
import React from 'react'

const STATUS = {
  checking: { label: 'Checking backend…', cls: 'status--checking' },
  online:   { label: 'Backend online',    cls: 'status--online' },
  offline:  { label: 'Demo mode · backend offline', cls: 'status--offline' },
}

function Logo() {
  return (
    <svg className="logo" viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="#ffffff" />
      <g stroke="#0b2545" strokeWidth="1.8" strokeLinecap="round">
        <line x1="16" y1="9" x2="8.5" y2="22" />
        <line x1="16" y1="9" x2="23.5" y2="22" />
        <line x1="8.5" y1="22" x2="23.5" y2="22" />
      </g>
      <circle cx="16" cy="9" r="3.4" fill="#0b2545" />
      <circle cx="8.5" cy="22" r="3.4" fill="#2563eb" />
      <circle cx="23.5" cy="22" r="3.4" fill="#2563eb" />
    </svg>
  )
}

export default function Header({ status, onReset, canReset }) {
  const s = STATUS[status] || STATUS.checking
  return (
    <header className="header">
      <div className="container header__inner">
        <div className="brand">
          <Logo />
          <div>
            <h1 className="brand__name">Agentic AI Copilot</h1>
            <p className="brand__tag">Learn, design and build agentic systems</p>
          </div>
        </div>
        <div className="header__actions">
          <span className={`status ${s.cls}`} role="status" title={s.label}>
            <span className="status__dot" />
            <span className="status__text">{s.label}</span>
          </span>
          <button type="button" className="btn btn--ghost" onClick={onReset} disabled={!canReset}>
            New chat
          </button>
        </div>
      </div>
    </header>
  )
}
