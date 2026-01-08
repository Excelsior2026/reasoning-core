import { useEffect, useRef } from 'react'
import cytoscape from 'cytoscape'

export function KnowledgeGraphViewer({ graph }) {
  const containerRef = useRef(null)
  const cyRef = useRef(null)

  useEffect(() => {
    if (!graph || !containerRef.current) return

    const nodes = (graph.nodes || []).map((node) => ({
      data: {
        id: node.id,
        label: node.label,
        type: node.type,
        confidence: node.confidence,
      },
      style: {
        label: node.label,
        backgroundColor: getNodeColor(node.type),
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
        lineColor: '#666',
        label: edge.type,
        fontSize: '10px',
        curveStyle: 'bezier',
      },
    }))

    // Destroy existing instance
    if (cyRef.current) {
      cyRef.current.destroy()
    }

    // Create new cytoscape instance
    cyRef.current = cytoscape({
      container: containerRef.current,
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
            'line-color': '#666',
            'target-arrow-color': '#666',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '10px',
            'text-rotation': 'autorotate',
            'text-margin-y': -10,
          },
        },
      ],
      layout: {
        name: 'cose',
        idealEdgeLength: 100,
        nodeOverlap: 20,
        refresh: 20,
        fit: true,
        padding: 30,
        randomize: false,
        componentSpacing: 100,
        nodeRepulsion: 4000000,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 80,
        numIter: 1000,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0,
      },
    })

    // Make graph interactive
    cyRef.current.on('tap', 'node', function (evt) {
      const node = evt.target
      // Only log in development
      if (process.env.NODE_ENV === 'development') {
        console.log('Selected node:', node.data())
      }
    })

    // Cleanup on unmount
    return () => {
      if (cyRef.current) {
        cyRef.current.destroy()
      }
    }
  }, [graph])

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

  return (
    <div className="w-full">
      <div
        ref={containerRef}
        className="w-full h-[600px] border border-gray-300 rounded-lg bg-white"
        style={{ minHeight: '600px' }}
      />
      <div className="mt-2 text-sm text-gray-600">
        <p>💡 Click and drag nodes to explore • Scroll to zoom</p>
      </div>
    </div>
  )
}
