// frontend/src/components/GraphViewer.jsx
// Owner: Oussema
// Interactive view of state["graph"] (built by graph/queries.py::query_subgraph):
//   nodes [{id, label, type, df, seed}]   seed = entity named in the question
//   edges [{source, target, relation, confidence, evidence, chunk_id}]
// Drag nodes, scroll to zoom, click a concept to list its relations and their evidence.
import React, { useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { typeColor } from '../lib/constants'

const HEIGHT = 380
const MAX_ZOOM = 2.5            // a graph of 2-3 concepts must not be zoomed to a huge size

function radius(node) {
  const mentions = node.df ? Math.min(Math.log10(node.df + 1) * 1.6, 5) : 0
  return 4.5 + mentions + (node.seed ? 3 : 0)
}

export default function GraphViewer({ data }) {
  const wrapRef = useRef(null)
  const fgRef = useRef(null)
  const fitted = useRef(false)
  const [width, setWidth] = useState(640)
  const [selected, setSelected] = useState(null)

  // force-graph mutates what it receives (edges get node objects): give it copies
  const graph = useMemo(() => {
    const nodes = (data?.nodes || []).map(n => ({ ...n }))
    const ids = new Set(nodes.map(n => n.id))
    const links = (data?.edges || []).filter(e => ids.has(e.source) && ids.has(e.target)).map(e => ({ ...e }))
    return { nodes, links }
  }, [data])

  const labelOf = useMemo(() => Object.fromEntries((data?.nodes || []).map(n => [n.id, n.label || n.id])), [data])
  const types = useMemo(() => [...new Set((data?.nodes || []).map(n => n.type).filter(Boolean))], [data])

  useEffect(() => {
    const el = wrapRef.current
    if (!el || typeof ResizeObserver === 'undefined') return
    const ro = new ResizeObserver(([entry]) => setWidth(Math.max(280, Math.floor(entry.contentRect.width))))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    fitted.current = false
    setSelected(null)
    fgRef.current?.d3Force('charge')?.strength(-260)       // spread the concepts out
    fgRef.current?.d3Force('link')?.distance(80)
  }, [graph])

  if (graph.nodes.length === 0) {
    return (
      <p className="empty">
        No graph for this question: no concept of the knowledge graph was recognised, the graph option is off,
        or Neo4j is not available.
      </p>
    )
  }

  const selectedNode = graph.nodes.find(n => n.id === selected)
  const relations = (data.edges || []).filter(e => e.source === selected || e.target === selected)

  function drawNode(node, ctx, scale) {
    const r = radius(node)
    if (node.seed || node.id === selected) {
      ctx.beginPath()
      ctx.arc(node.x, node.y, r + 3, 0, 2 * Math.PI)
      ctx.fillStyle = node.id === selected ? '#93c5fd' : '#dbeafe'
      ctx.fill()
    }
    ctx.beginPath()
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI)
    ctx.fillStyle = typeColor(node.type)
    ctx.fill()
    ctx.font = `${(node.seed ? 12 : 10.5) / scale}px system-ui, sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    ctx.fillStyle = '#0b1b33'
    ctx.fillText(node.label || node.id, node.x, node.y + r + 3 / scale)
  }

  function drawLinkLabel(link, ctx, scale) {
    const s = link.source
    const t = link.target
    if (scale < 1.5 || typeof s !== 'object' || typeof t !== 'object') return
    ctx.font = `${9 / scale}px system-ui, sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillStyle = '#64748b'
    ctx.fillText(link.relation, (s.x + t.x) / 2, (s.y + t.y) / 2)
  }

  return (
    <div className="graph">
      <div className="graph__canvas" ref={wrapRef}>
        <ForceGraph2D
          ref={fgRef}
          graphData={graph}
          width={width}
          height={HEIGHT}
          backgroundColor="#f8fafc"
          nodeId="id"
          nodeCanvasObject={drawNode}
          nodePointerAreaPaint={(node, color, ctx) => {
            ctx.fillStyle = color
            ctx.beginPath()
            ctx.arc(node.x, node.y, radius(node) + 3, 0, 2 * Math.PI)
            ctx.fill()
          }}
          linkColor={() => '#b8c5db'}
          linkWidth={l => 0.6 + (l.confidence || 0.5) * 1.4}
          linkDirectionalArrowLength={3.5}
          linkDirectionalArrowRelPos={1}
          linkLabel={l => `${labelOf[l.source.id ?? l.source]} ${l.relation} ${labelOf[l.target.id ?? l.target]}`}
          linkCanvasObjectMode={() => 'after'}
          linkCanvasObject={drawLinkLabel}
          cooldownTicks={90}
          onEngineStop={() => {
            if (!fitted.current) {
              fitted.current = true
              fgRef.current?.zoomToFit(400, 40)
              setTimeout(() => {
                const fg = fgRef.current
                if (fg && fg.zoom() > MAX_ZOOM) fg.zoom(MAX_ZOOM, 300)
              }, 450)
            }
          }}
          onNodeClick={n => setSelected(s => (s === n.id ? null : n.id))}
          onBackgroundClick={() => setSelected(null)}
        />
      </div>

      <div className="graph__legend">
        {types.map(t => (
          <span key={t} className="legend__item">
            <span className="legend__dot" style={{ background: typeColor(t) }} />{t}
          </span>
        ))}
        <span className="legend__item legend__item--seed"><span className="legend__ring" />named in your question</span>
      </div>

      <div className="graph__details">
        {selectedNode ? (
          <>
            <div className="graph__title">
              <strong>{selectedNode.label}</strong>
              {selectedNode.type && <span className="pill">{selectedNode.type}</span>}
              {selectedNode.df ? <span className="muted">mentioned in {selectedNode.df} passages</span> : null}
            </div>
            {relations.length === 0 ? (
              <p className="muted">No relation to the other concepts shown.</p>
            ) : (
              <ul className="relations">
                {relations.map((e, i) => (
                  <li key={i}>
                    <span className="relations__triple">
                      {labelOf[e.source]} <b>{e.relation}</b> {labelOf[e.target]}
                    </span>
                    {e.confidence != null && <span className="muted"> · {Math.round(e.confidence * 100)}%</span>}
                    {e.evidence && <q className="relations__evidence">{e.evidence}</q>}
                  </li>
                ))}
              </ul>
            )}
          </>
        ) : (
          <p className="muted">
            {graph.nodes.length} concept{graph.nodes.length > 1 ? 's' : ''} · {graph.links.length} relation{graph.links.length !== 1 ? 's' : ''}. Click a concept to see how it connects
            and the passage that proves it.
          </p>
        )}
      </div>
    </div>
  )
}
