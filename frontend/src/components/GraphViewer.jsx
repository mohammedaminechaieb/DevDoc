// frontend/src/components/GraphViewer.jsx
// Owner: Aya
// TODO: render data.nodes / data.edges with an interactive graph library (e.g. react-force-graph)
import React from 'react'

export default function GraphViewer({ data }) {
  if (!data || !data.nodes || data.nodes.length === 0) return null
  return (
    <div>
      <h3>Knowledge Graph</h3>
      <p>{data.nodes.length} concepts, {data.edges.length} relations - visualization coming soon.</p>
    </div>
  )
}
