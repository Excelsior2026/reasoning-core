import { useState, useEffect, useRef } from 'react'
import cytoscape from 'cytoscape'

export function GraphComparison({ graph1, graph2, graph1Label = 'Graph 1', graph2Label = 'Graph 2' }) {
  const container1Ref = useRef(null)
  const container2Ref = useRef(null)
  const cy1Ref = useRef(null)
  const cy2Ref = useRef(null)
  const [comparisonMode, setComparisonMode] = useState('side-by-side') // 'side-by-side', 'diff', 'merged'
  const [diffStats, setDiffStats] = useState(null)

  useEffect(() => {
    if (!graph1 || !graph2) return

    // Calculate diff statistics
    const nodes1 = new Set((graph1.nodes || []).map(n => `${n.label}:${n.type}`))
    const nodes2 = new Set((graph2.nodes || []).map(n => `${n.label}:${n.type}`))
    
    const edges1 = new Set((graph1.edges || []).map(e => `${e.source_id}:${e.target_id}:${e.type}`))
    const edges2 = new Set((graph2.edges || []).map(e => `${e.source_id}:${e.target_id}:${e.type}`))

    const commonNodes = [...nodes1].filter(n => nodes2.has(n)).length
    const onlyIn1Nodes = [...nodes1].filter(n => !nodes2.has(n)).length
    const onlyIn2Nodes = [...nodes2].filter(n => !nodes1.has(n)).length

    const commonEdges = [...edges1].filter(e => edges2.has(e)).length
    const onlyIn1Edges = [...edges1].filter(e => !edges2.has(e)).length
    const onlyIn2Edges = [...edges2].filter(e => !edges1.has(e)).length

    setDiffStats({
      nodes: { common: commonNodes, only1: onlyIn1Nodes, only2: onlyIn2Nodes },
      edges: { common: commonEdges, only1: onlyIn1Edges, only2: onlyIn2Edges },
    })
  }, [graph1, graph2])

  const getNodeColor = (type) => {
    const colorMap = {
      symptom: '#FF6B6B',
      disease: '#FF8E53',
      treatment: '#4ECDC4',
      test: '#45B7D1',
      strategy: '#96CEB4',
      metric: '#FFEAA7',
      pain_points: '#FF7675',
      agenda_items: '#74B9FF',
      action_items: '#00B894',
      decisions: '#FDCB6E',
    }
    return colorMap[type] || '#95A5A6'
  }

  const renderGraph = (container, graph, cyRef, highlightColor = null) => {
    if (!container || !graph) return

    if (cyRef.current) {
      cyRef.current.destroy()
    }

    const nodes = (graph.nodes || []).map((node) => ({
      data: {
        id: node.id,
        label: node.label,
        type: node.type,
        confidence: node.confidence,
        highlightColor,
      },
      style: {
        label: node.label,
        backgroundColor: highlightColor || getNodeColor(node.type),
        shape: 'round-rectangle',
        width: 'label',
        height: 'label',
        padding: '10px',
      },
    }))

    const edges = (graph.edges || []).map((edge, idx) => ({
      data: {
        id: `e${idx}`,
        source: edge.source_id,
        target: edge.target_id,
        label: edge.type,
      },
      style: {
        width: 2,
        lineColor: highlightColor || '#666',
        label: edge.type,
        fontSize: '10px',
        curveStyle: 'bezier',
      },
    }))

    cyRef.current = cytoscape({
      container,
      elements: [...nodes, ...edges],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(backgroundColor)',
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '12px',
            'font-weight': 'bold',
            'color': '#333',
            'border-width': 2,
            'border-color': '#333',
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': highlightColor || '#666',
            'target-arrow-color': highlightColor || '#666',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '10px',
          },
        },
      ],
      layout: {
        name: 'cose',
        fit: true,
        padding: 30,
      },
    })

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy()
      }
    }
  }

  useEffect(() => {
    if (comparisonMode === 'side-by-side' || comparisonMode === 'diff') {
      if (graph1 && container1Ref.current) {
        renderGraph(container1Ref.current, graph1, cy1Ref, comparisonMode === 'diff' ? '#3b82f6' : null)
      }
      if (graph2 && container2Ref.current) {
        renderGraph(container2Ref.current, graph2, cy2Ref, comparisonMode === 'diff' ? '#10b981' : null)
      }
    } else if (comparisonMode === 'merged' && graph1 && graph2 && container1Ref.current) {
      // Merge graphs
      const mergedGraph = {
        nodes: [...(graph1.nodes || []), ...(graph2.nodes || [])],
        edges: [...(graph1.edges || []), ...(graph2.edges || [])],
      }
      renderGraph(container1Ref.current, mergedGraph, cy1Ref)
    }
  }, [graph1, graph2, comparisonMode])

  if (!graph1 || !graph2) {
    return (
      <div className="p-8 text-center text-gray-500">
        Select two analyses to compare
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Comparison Mode Selector */}
      <div className="flex gap-2 p-2 bg-gray-50 rounded-lg">
        <button
          onClick={() => setComparisonMode('side-by-side')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            comparisonMode === 'side-by-side'
              ? 'bg-indigo-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Side-by-Side
        </button>
        <button
          onClick={() => setComparisonMode('diff')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            comparisonMode === 'diff'
              ? 'bg-indigo-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Diff View
        </button>
        <button
          onClick={() => setComparisonMode('merged')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            comparisonMode === 'merged'
              ? 'bg-indigo-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Merged
        </button>
      </div>

      {/* Diff Statistics */}
      {diffStats && comparisonMode === 'diff' && (
        <div className="grid grid-cols-3 gap-4 p-4 bg-white border border-gray-200 rounded-lg">
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Nodes</h4>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Common:</span>
                <span className="font-semibold text-indigo-600">{diffStats.nodes.common}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Only in {graph1Label}:</span>
                <span className="font-semibold text-blue-600">{diffStats.nodes.only1}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Only in {graph2Label}:</span>
                <span className="font-semibold text-green-600">{diffStats.nodes.only2}</span>
              </div>
            </div>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Edges</h4>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Common:</span>
                <span className="font-semibold text-indigo-600">{diffStats.edges.common}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Only in {graph1Label}:</span>
                <span className="font-semibold text-blue-600">{diffStats.edges.only1}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Only in {graph2Label}:</span>
                <span className="font-semibold text-green-600">{diffStats.edges.only2}</span>
              </div>
            </div>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Similarity</h4>
            <div className="text-sm">
              <div className="text-2xl font-bold text-indigo-600">
                {graph1.nodes && graph2.nodes
                  ? ((diffStats.nodes.common / Math.max(graph1.nodes.length, graph2.nodes.length)) * 100).toFixed(1)
                  : 0}%
              </div>
              <div className="text-gray-600">Node similarity</div>
            </div>
          </div>
        </div>
      )}

      {/* Graph Views */}
      {comparisonMode === 'side-by-side' && (
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-gray-900">{graph1Label}</h3>
            <div
              ref={container1Ref}
              className="w-full h-[500px] border border-gray-300 rounded-lg bg-white"
            />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-gray-900">{graph2Label}</h3>
            <div
              ref={container2Ref}
              className="w-full h-[500px] border border-gray-300 rounded-lg bg-white"
            />
          </div>
        </div>
      )}

      {comparisonMode === 'diff' && (
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-blue-600">{graph1Label}</h3>
            <div
              ref={container1Ref}
              className="w-full h-[500px] border-2 border-blue-300 rounded-lg bg-white"
            />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-green-600">{graph2Label}</h3>
            <div
              ref={container2Ref}
              className="w-full h-[500px] border-2 border-green-300 rounded-lg bg-white"
            />
          </div>
        </div>
      )}

      {comparisonMode === 'merged' && (
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-gray-900">Merged Graph</h3>
          <div
            ref={container1Ref}
            className="w-full h-[600px] border border-gray-300 rounded-lg bg-white"
          />
        </div>
      )}
    </div>
  )
}
