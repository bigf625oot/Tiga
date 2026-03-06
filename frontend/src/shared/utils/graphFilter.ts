export type Nodes = Record<string, { type?: string }>
export type Edges = Record<string, { source: string; target: string; label?: string }>

export function filterEdges(nodes: Nodes, edges: Edges, hiddenTypes: string[]): Edges {
  if (!edges || !nodes) return {}
  const hidden = new Set(Object.keys(nodes).filter(id => hiddenTypes.includes((nodes[id].type || '').toLowerCase())))
  const out: Edges = {}
  Object.keys(edges).forEach(id => {
    const e = edges[id]
    if (hidden.has(e.source) || hidden.has(e.target)) return
    out[id] = e
  })
  return out
}
