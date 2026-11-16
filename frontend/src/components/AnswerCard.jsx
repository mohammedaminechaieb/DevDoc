// frontend/src/components/AnswerCard.jsx
// Owner: Oussema
// Renders the answer as Markdown. Inline citations [n] become buttons that open source n.
import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/** [1] -> link to #source-1, but never inside code. */
function linkCitations(markdown) {
  return markdown
    .split(/(```[\s\S]*?```|`[^`\n]*`)/g)
    .map((part, i) => (i % 2 === 1 ? part : part.replace(/\[(\d{1,2})\](?!\()/g, '[[$1]](#source-$1)')))
    .join('')
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

function CodeBlock({ lang, code }) {
  const [copied, setCopied] = useState(false)
  async function copy() {
    if (await copyText(code)) {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    }
  }
  return (
    <div className="code">
      <div className="code__bar">
        <span>{lang || 'code'}</span>
        <button type="button" onClick={copy}>{copied ? 'Copied' : 'Copy'}</button>
      </div>
      <pre><code>{code}</code></pre>
    </div>
  )
}

export default function AnswerCard({ answer, onCite }) {
  const [copied, setCopied] = useState(false)

  const components = {
    a({ href, children }) {
      const m = /^#source-(\d+)$/.exec(href || '')
      if (m) {
        return <button type="button" className="cite" onClick={() => onCite?.(Number(m[1]))}>{m[1]}</button>
      }
      return <a href={href} target="_blank" rel="noreferrer">{children}</a>
    },
    pre({ children }) {
      const child = React.Children.toArray(children)[0]
      const lang = /language-([\w+-]+)/.exec(child?.props?.className || '')?.[1] || ''
      const code = String(child?.props?.children ?? '').replace(/\n$/, '')
      return <CodeBlock lang={lang} code={code} />
    },
  }

  async function copyAll() {
    if (await copyText(answer)) {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    }
  }

  return (
    <article className="answer">
      <div className="markdown">
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
          {linkCitations(answer || '')}
        </ReactMarkdown>
      </div>
      <div className="answer__tools">
        <button type="button" className="answer__copy" onClick={copyAll}>{copied ? 'Copied' : 'Copy answer'}</button>
      </div>
    </article>
  )
}
