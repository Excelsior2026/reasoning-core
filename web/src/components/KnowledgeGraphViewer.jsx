import { useEffect, useRef, useState, useCallback } from 'react'
import cytoscape from 'cytoscape'

export function KnowledgeGraphViewer({ graph, onNodeFilter }) {
  const containerRef = useRef(null)
  const cyRef = useRef(null)
  const [layout, setLayout] = useState('cose')
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedEdge, setSelectedEdge] = useState(null)
  const [filteredTypes, setFilteredTypes] = useState(new Set())
  const [highlightedPath, setHighlightedPath] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [hoveredNode, setHoveredNode] = useState(null)

  useEffect(() => {
    if (!graph || !containerRef.current) return

    // Filter nodes by type if filter is active
    const nodes = (graph.nodes || [])
      .filter((node) => filteredTypes.size === 0 || filteredTypes.has(node.type))
      .map((node) => ({
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

    // Filter edges to only include those with valid nodes
    const validNodeIds = new Set(nodes.map(n => n.data.id))
    const edges = (graph.edges || [])
      .filter((edge) => validNodeIds.has(edge.source_id) && validNodeIds.has(edge.target_id))
      .map((edge, idx) => ({
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
            'width': 'mapData(confidence, 0, 1, 50, 150)',
            'height': 'mapData(confidence, 0, 1, 50, 150)',
          },
        },
        {
          selector: 'node.highlighted',
          style: {
            'border-width': 4,
            'border-color': '#3b82f6',
            'opacity': 1,
          },
        },
        {
          selector: 'node.selected',
          style: {
            'border-width': 5,
            'border-color': '#1e40af',
            'background-color': '#dbeafe',
          },
        },
        {
          selector: 'node.search-match',
          style: {
            'border-width': 3,
            'border-color': '#f59e0b',
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 'mapData(confidence, 0, 1, 1, 5)',
            'line-color': '#666',
            'target-arrow-color': '#666',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '10px',
            'text-rotation': 'autorotate',
            'text-margin-y': -10,
            'opacity': 0.7,
          },
        },
        {
          selector: 'edge.highlighted',
          style: {
            'width': 4,
            'line-color': '#3b82f6',
            'target-arrow-color': '#3b82f6',
            'opacity': 1,
          },
        },
        {
          selector: 'edge.selected',
          style: {
            'width': 5,
            'line-color': '#1e40af',
            'target-arrow-color': '#1e40af',
            'opacity': 1,
          },
        },
      ],
      layout: getLayoutConfig(layout),
    })

    // Make graph interactive
    cyRef.current.on('tap', 'node', function (evt) {
      const node = evt.target
      const nodeData = node.data()
      setSelectedNode(nodeData)
      if (onNodeFilter) {
        onNodeFilter(nodeData)
      }
      
      // Highlight connected nodes
      const connected = node.neighborhood('node')
      cyRef.current.nodes().removeClass('highlighted')
      cyRef.current.edges().removeClass('highlighted')
      connected.addClass('highlighted')
      node.addClass('selected')
      connected.connectedEdges().addClass('highlighted')
    })

    cyRef.current.on('tap', function (evt) {
      if (evt.target === cyRef.current) {
        setSelectedNode(null)
        setSelectedEdge(null)
        cyRef.current.nodes().removeClass('highlighted selected')
        cyRef.current.edges().removeClass('highlighted')
      }
    })

    cyRef.current.on('tap', 'edge', function (evt) {
      const edge = evt.target
      setSelectedEdge(edge.data())
      cyRef.current.edges().removeClass('selected')
      edge.addClass('selected')
    })

    cyRef.current.on('mouseover', 'node', function (evt) {
      const node = evt.target
      setHoveredNode(node.data())
    })

    cyRef.current.on('mouseout', 'node', function (evt) {
      setHoveredNode(null)
    })

    // Search functionality
    if (searchTerm) {
      cyRef.current.nodes().forEach((node) => {
        const nodeData = node.data()
        const matches = nodeData.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
                       nodeData.type.toLowerCase().includes(searchTerm.toLowerCase())
        if (matches) {
          node.addClass('search-match')
        } else {
          node.removeClass('search-match')
        }
      })
    } else {
      cyRef.current.nodes().removeClass('search-match')
    }

    // Cleanup on unmount
    return () => {
      if (cyRef.current) {
        cyRef.current.destroy()
      }
    }
  }, [graph, layout, filteredTypes])

  const getLayoutConfig = (layoutName) => {
    const configs = {
      cose: {
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
      circle: {
        name: 'circle',
        fit: true,
        padding: 30,
        radius: null,
        startAngle: 0,
        sweep: null,
        clockwise: true,
        sort: undefined,
      },
      grid: {
        name: 'grid',
        fit: true,
        padding: 30,
        avoidOverlap: true,
        avoidOverlapPadding: 10,
        nodeDimensionsIncludeLabels: false,
        condense: false,
        rows: undefined,
        cols: undefined,
        position: undefined,
        sort: undefined,
      },
      breadthfirst: {
        name: 'breadthfirst',
        fit: true,
        directed: false,
        padding: 30,
        circle: false,
        spacingFactor: 1.75,
        avoidOverlap: true,
        nodeDimensionsIncludeLabels: false,
        roots: undefined,
        maximalAdjustments: 0,
      },
    }
    return configs[layoutName] || configs.cose
  }

  const toggleNodeTypeFilter = (type) => {
    const newFiltered = new Set(filteredTypes)
    if (newFiltered.has(type)) {
      newFiltered.delete(type)
    } else {
      newFiltered.add(type)
    }
    setFilteredTypes(newFiltered)
  }

  const getAvailableTypes = () => {
    if (!graph?.nodes) return []
    const types = new Set(graph.nodes.map(n => n.type))
    return Array.from(types).sort()
  }

  const resetZoom = () => {
    if (cyRef.current) {
      cyRef.current.fit()
    }
  }

  const centerGraph = () => {
    if (cyRef.current) {
      cyRef.current.center()
      cyRef.current.fit()
    }
  }

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

  const availableTypes = getAvailableTypes()
  
  const handleSearch = useCallback((term) => {
    setSearchTerm(term)
    if (cyRef.current) {
      if (term) {
        cyRef.current.nodes().forEach((node) => {
          const nodeData = node.data()
          const matches = nodeData.label.toLowerCase().includes(term.toLowerCase()) ||
                         nodeData.type.toLowerCase().includes(term.toLowerCase())
          if (matches) {
            node.addClass('search-match')
          } else {
            node.removeClass('search-match')
          }
        })
      } else {
        cyRef.current.nodes().removeClass('search-match')
      }
    }
  }, [])

  const findPath = useCallback((sourceId, targetId) => {
    if (!cyRef.current) return []
    
    const source = cyRef.current.getElementById(sourceId)
    const target = cyRef.current.getElementById(targetId)
    
    if (!source || !target) return []
    
    const path = source.pathTo(target)
    const nodes = path.nodes()
    const edges = path.edges()
    
    // Highlight path
    cyRef.current.nodes().removeClass('path-highlight')
    cyRef.current.edges().removeClass('path-highlight')
    nodes.addClass('path-highlight')
    edges.addClass('path-highlight')
    
    setHighlightedPath(nodes.map(n => n.id()))
    
    // Center on path
    cyRef.current.fit(nodes, 100)
    
    return nodes.map(n => n.data())
  }, [])

  const clearHighlight = useCallback(() => {
    if (cyRef.current) {
      cyRef.current.nodes().removeClass('path-highlight')
      cyRef.current.edges().removeClass('path-highlight')
      setHighlightedPath([])
    }
  }, [])

  return (
    <div className="w-full space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap gap-4 p-4 bg-gray-50 rounded-lg">
        {/* Search */}
        <div className="flex-1 min-w-[200px]">
          <label className="block text-sm font-medium text-gray-700 mb-1">Search:</label>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search nodes..."
            className="w-full px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Layout:</label>
          <select
            value={layout}
            onChange={(e) => setLayout(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-indigo-500"
          >
            <option value="cose">COSE</option>
            <option value="circle">Circle</option>
            <option value="grid">Grid</option>
            <option value="breadthfirst">Breadthfirst</option>
          </select>
        </div>
        <button
          onClick={resetZoom}
          className="px-3 py-1 bg-white border border-gray-300 rounded-md text-sm hover:bg-gray-50"
        >
          Reset Zoom
        </button>
        <button
          onClick={centerGraph}
          className="px-3 py-1 bg-white border border-gray-300 rounded-md text-sm hover:bg-gray-50"
        >
          Center
        </button>
        {availableTypes.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-gray-700">Filter:</span>
            {availableTypes.map((type) => (
              <button
                key={type}
                onClick={() => toggleNodeTypeFilter(type)}
                className={`px-2 py-1 rounded text-xs transition-colors ${
                  filteredTypes.has(type)
                    ? 'bg-red-100 text-red-700 border border-red-300'
                    : 'bg-white border border-gray-300 hover:bg-gray-50'
                }`}
              >
                {type}
                {filteredTypes.has(type) && ' ✕'}
              </button>
            ))}
            {filteredTypes.size > 0 && (
              <button
                onClick={() => setFilteredTypes(new Set())}
                className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs border border-indigo-300 hover:bg-indigo-200"
              >
                Clear Filters
              </button>
            )}
          </div>
        )}
      </div>

      {/* Graph Container */}
      <div className="relative">
        <div
          ref={containerRef}
          className="w-full h-[600px] border border-gray-300 rounded-lg bg-white"
          style={{ minHeight: '600px' }}
        />
        {/* Node Details Panel */}
        {(selectedNode || hoveredNode) && (
          <div className="absolute top-4 right-4 p-4 bg-white border border-gray-300 rounded-lg shadow-lg max-w-xs z-10">
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-semibold text-gray-900">Node Details</h4>
              <button
                onClick={() => {
                  setSelectedNode(null)
                  if (cyRef.current) {
                    cyRef.current.nodes().removeClass('selected highlighted')
                    cyRef.current.edges().removeClass('highlighted')
                  }
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            {(() => {
              const node = selectedNode || hoveredNode
              return (
                <>
                  <p className="text-sm font-medium text-gray-900 mb-1">{node.label}</p>
                  <p className="text-xs text-gray-600 mb-1">
                    Type: <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded">{node.type}</span>
                  </p>
                  {node.confidence && (
                    <div className="mt-2">
                      <p className="text-xs text-gray-600 mb-1">Confidence:</p>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-indigo-600 h-2 rounded-full"
                          style={{ width: `${(node.confidence * 100)}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{(node.confidence * 100).toFixed(1)}%</p>
                    </div>
                  )}
                  {node.properties?.context && (
                    <div className="mt-2">
                      <p className="text-xs text-gray-600 mb-1">Context:</p>
                      <p className="text-xs text-gray-500 italic line-clamp-3">{node.properties.context}</p>
                    </div>
                  )}
                </>
              )
            })()}
          </div>
        )}

        {/* Edge Details Panel */}
        {selectedEdge && (
          <div className="absolute bottom-4 right-4 p-4 bg-white border border-gray-300 rounded-lg shadow-lg max-w-xs z-10">
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-semibold text-gray-900">Relationship Details</h4>
              <button
                onClick={() => {
                  setSelectedEdge(null)
                  if (cyRef.current) {
                    cyRef.current.edges().removeClass('selected')
                  }
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            <p className="text-sm font-medium text-gray-900 mb-1">
              {selectedEdge.source} → {selectedEdge.target}
            </p>
            <p className="text-xs text-gray-600 mb-1">
              Type: <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded">{selectedEdge.label}</span>
            </p>
          </div>
        )}
      </div>

      <div className="text-sm text-gray-600">
        <p>💡 Click and drag nodes to explore • Scroll to zoom • Click nodes/edges for details • Search to filter</p>
      </div>
    </div>
  )
}
