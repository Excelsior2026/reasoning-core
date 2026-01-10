import { useState, useEffect, useCallback } from 'react'
import { FileUpload } from './components/FileUpload'
import { URLInput } from './components/URLInput'
import { TextInput } from './components/TextInput'
import { ResultsDisplay } from './components/ResultsDisplay'
import { KnowledgeGraphViewer } from './components/KnowledgeGraphViewer'
import { StatisticsPanel } from './components/StatisticsPanel'
import { ExportPanel } from './components/ExportPanel'
import { DetailedView } from './components/DetailedView'
import { HistoryPanel } from './components/HistoryPanel'
import { SettingsPanel } from './components/SettingsPanel'
import { SearchFilter } from './components/SearchFilter'

function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('file') // 'file', 'url', 'text'
  const [resultsView, setResultsView] = useState('summary') // 'summary', 'detailed', 'graph', 'compare'
  const [searchTerm, setSearchTerm] = useState('')
  const [filterOptions, setFilterOptions] = useState({})
  const [saveToHistoryFn, setSaveToHistoryFn] = useState(null)
  const [settings, setSettings] = useState({})
  const [comparisonGraph1, setComparisonGraph1] = useState(null)
  const [comparisonGraph2, setComparisonGraph2] = useState(null)
  const [searchResults, setSearchResults] = useState(null)

  const handleSearchResults = (results) => {
    setSearchResults(results)
  }

  // Set current graph as default for comparison
  useEffect(() => {
    if (results && results.result?.knowledge_graph && !comparisonGraph1) {
      setComparisonGraph1(results.result.knowledge_graph)
    }
  }, [results, comparisonGraph1])

  const handleResults = useCallback((data) => {
    // Handle both direct results and task-based results
    const resultData = data.result ? data : { result: data, task_id: data.task_id }
    setResults(resultData)
    setLoading(false)
    setError(null)
    
    // Auto-save to history if enabled
    if (saveToHistoryFn && (settings.autoSave !== false)) {
      saveToHistoryFn(resultData)
    }
  }, [saveToHistoryFn, settings])

  const handleError = (err) => {
    setError(err)
    setLoading(false)
    setResults(null)
  }

  const handleStartLoading = () => {
    setLoading(true)
    setError(null)
    setResults(null)
  }

  const handleSearch = (term) => {
    setSearchTerm(term)
  }

  const handleFilterChange = (filters) => {
    setFilterOptions(filters)
  }

  const handleNodeFilter = (nodeData) => {
    // Could be used for additional filtering or highlighting
    console.log('Selected node:', nodeData)
  }

  const handleLoadHistory = useCallback((data) => {
    setResults(data)
    setResultsView('summary')
  }, [])

  const getFilteredData = () => {
    if (!results?.result) return results

    const { concepts, relationships } = results.result
    let filteredConcepts = concepts || []
    let filteredRelationships = relationships || []

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filteredConcepts = filteredConcepts.filter(
        (c) => c.text.toLowerCase().includes(term) || c.type.toLowerCase().includes(term)
      )
      filteredRelationships = filteredRelationships.filter(
        (r) =>
          r.source.text.toLowerCase().includes(term) ||
          r.target.text.toLowerCase().includes(term) ||
          r.type.toLowerCase().includes(term)
      )
    }

    // Apply type filter
    if (filterOptions.type && filterOptions.type !== 'all') {
      filteredConcepts = filteredConcepts.filter((c) => c.type === filterOptions.type)
    }

    return {
      ...results,
      result: {
        ...results.result,
        concepts: filteredConcepts,
        relationships: filteredRelationships,
      },
    }
  }

  const filteredResults = getFilteredData()

  // Get unique concept types for filter dropdown
  const conceptTypes = results?.result?.concepts
    ? Array.from(new Set(results.result.concepts.map((c) => c.type))).sort()
    : []

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-8 text-center">
          <div className="flex justify-between items-center mb-4">
            <div className="flex-1"></div>
            <div className="flex-1 text-center">
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                🧠 Reasoning Core
              </h1>
              <p className="text-gray-600 text-lg">
                Transform documents, websites, and text into intelligent knowledge graphs
              </p>
            </div>
            <div className="flex-1 flex justify-end">
              <SettingsPanel onSettingsChange={setSettings} />
            </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto">
          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            {/* Left Column - Input */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-lg p-6 sticky top-4">
                {/* Input Tabs */}
                <div className="mb-4 flex rounded-lg bg-gray-100 p-1">
                  <button
                    onClick={() => setActiveTab('file')}
                    className={`flex-1 px-4 py-2 rounded-md font-medium text-sm transition-colors ${
                      activeTab === 'file'
                        ? 'bg-white text-indigo-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    📄 File
                  </button>
                  <button
                    onClick={() => setActiveTab('url')}
                    className={`flex-1 px-4 py-2 rounded-md font-medium text-sm transition-colors ${
                      activeTab === 'url'
                        ? 'bg-white text-indigo-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    🌐 URL
                  </button>
                  <button
                    onClick={() => setActiveTab('text')}
                    className={`flex-1 px-4 py-2 rounded-md font-medium text-sm transition-colors ${
                      activeTab === 'text'
                        ? 'bg-white text-indigo-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    ✍️ Text
                  </button>
                </div>

                {activeTab === 'file' && (
                  <FileUpload
                    onResults={handleResults}
                    onError={handleError}
                    onStartLoading={handleStartLoading}
                    loading={loading}
                  />
                )}
                {activeTab === 'url' && (
                  <URLInput
                    onResults={handleResults}
                    onError={handleError}
                    onStartLoading={handleStartLoading}
                    loading={loading}
                  />
                )}
                {activeTab === 'text' && (
                  <TextInput
                    onResults={handleResults}
                    onError={handleError}
                    onStartLoading={handleStartLoading}
                    loading={loading}
                  />
                )}

                {error && (
                  <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-red-800 font-medium">Error:</p>
                    <p className="text-red-600 text-sm">{error}</p>
                  </div>
                )}

                {loading && (
                  <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-3"></div>
                      <p className="text-blue-800">Processing...</p>
                    </div>
                  </div>
                )}

                {/* History Panel */}
                <div className="mt-6">
                  <HistoryPanel 
                    onLoadHistory={(saveFn) => {
                      setSaveToHistoryFn(() => saveFn)
                    }}
                    onSelectHistory={(data) => {
                      handleLoadHistory(data)
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Right Column - Results */}
            <div className="lg:col-span-2 space-y-6">
              {/* Results View Tabs */}
              {results && (
                <div className="bg-white rounded-lg shadow-lg p-4">
                  <div className="flex border-b border-gray-200 mb-4">
                    {[
                      { id: 'summary', label: 'Summary' },
                      { id: 'detailed', label: 'Detailed View' },
                      { id: 'graph', label: 'Graph' },
                      { id: 'compare', label: 'Compare' },
                      { id: 'statistics', label: 'Statistics' },
                      { id: 'domain-builder', label: 'Domain Builder' },
                    ].map((tab) => (
                      <button
                        key={tab.id}
                        onClick={() => setResultsView(tab.id)}
                        className={`px-6 py-2 font-medium transition-colors ${
                          resultsView === tab.id
                            ? 'border-b-2 border-indigo-600 text-indigo-600'
                            : 'text-gray-600 hover:text-gray-900'
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  {/* Search and Filter */}
                  {(resultsView === 'detailed' || resultsView === 'summary') && (
                      <div className="mb-4">
                        <SearchFilter
                          onSearch={handleSearch}
                          onFilterChange={handleFilterChange}
                          filterOptions={conceptTypes}
                          taskId={results?.task_id}
                          onSearchResults={handleSearchResults}
                        />
                      </div>
                  )}

                  {/* Export Panel */}
                  {results && (
                    <div className="mb-4">
                      <ExportPanel data={results} />
                    </div>
                  )}
                </div>
              )}

              {/* Results Content */}
              <div className="bg-white rounded-lg shadow-lg p-6">
                {results ? (
                  <>
                    {resultsView === 'summary' && (
                      <div className="space-y-4">
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                          Analysis Results
                        </h2>
                        <ResultsDisplay results={filteredResults} />
                      </div>
                    )}

                    {resultsView === 'detailed' && (
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                          Detailed Analysis
                        </h2>
                        <DetailedView results={filteredResults} searchResults={searchResults} />
                      </div>
                    )}

                    {resultsView === 'graph' && results.result.knowledge_graph && (
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                          Knowledge Graph Visualization
                        </h2>
                        <KnowledgeGraphViewer
                          graph={results.result.knowledge_graph}
                          onNodeFilter={handleNodeFilter}
                        />
                      </div>
                    )}

                    {resultsView === 'compare' && (
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                          Graph Comparison
                        </h2>
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-2">
                                Select First Graph (from history)
                              </label>
                              <select
                                onChange={(e) => {
                                  const value = e.target.value
                                  if (value) {
                                    const history = JSON.parse(localStorage.getItem('reasoning-core-history') || '[]')
                                    const item = history.find(h => h.id === value)
                                    if (item?.data?.result?.knowledge_graph) {
                                      setComparisonGraph1(item.data.result.knowledge_graph)
                                    }
                                  } else {
                                    setComparisonGraph1(results?.result?.knowledge_graph || null)
                                  }
                                }}
                                className="w-full px-4 py-2 border border-gray-300 rounded-md"
                              >
                                <option value="">Current Analysis</option>
                                {(() => {
                                  try {
                                    const history = JSON.parse(localStorage.getItem('reasoning-core-history') || '[]')
                                    return history.filter(h => h.data?.result?.knowledge_graph).map(h => (
                                      <option key={h.id} value={h.id}>
                                        {h.source?.filename || h.source?.url || 'Text'} - {new Date(h.timestamp).toLocaleDateString()}
                                      </option>
                                    ))
                                  } catch {
                                    return []
                                  }
                                })()}
                              </select>
                            </div>
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-2">
                                Select Second Graph (from history)
                              </label>
                              <select
                                onChange={(e) => {
                                  const value = e.target.value
                                  if (value) {
                                    const history = JSON.parse(localStorage.getItem('reasoning-core-history') || '[]')
                                    const item = history.find(h => h.id === value)
                                    if (item?.data?.result?.knowledge_graph) {
                                      setComparisonGraph2(item.data.result.knowledge_graph)
                                    }
                                  }
                                }}
                                className="w-full px-4 py-2 border border-gray-300 rounded-md"
                              >
                                <option value="">Select from history...</option>
                                {(() => {
                                  try {
                                    const history = JSON.parse(localStorage.getItem('reasoning-core-history') || '[]')
                                    return history.filter(h => h.data?.result?.knowledge_graph).map(h => (
                                      <option key={h.id} value={h.id}>
                                        {h.source?.filename || h.source?.url || 'Text'} - {new Date(h.timestamp).toLocaleDateString()}
                                      </option>
                                    ))
                                  } catch {
                                    return []
                                  }
                                })()}
                              </select>
                            </div>
                          </div>
                          <GraphComparison
                            graph1={comparisonGraph1 || results?.result?.knowledge_graph}
                            graph2={comparisonGraph2}
                            graph1Label="Current Analysis"
                            graph2Label="Selected History"
                          />
                        </div>
                      </div>
                    )}

                    {resultsView === 'statistics' && (
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                          Statistics & Insights
                        </h2>
                        <StatisticsPanel results={results} taskId={results?.task_id} />
                      </div>
                    )}

                    {resultsView === 'domain-builder' && (
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                          Custom Domain Builder
                        </h2>
                        <p className="text-gray-600 mb-4">
                          Create custom domains with specific concept types and extraction patterns.
                          Define your own domain-specific rules for concept extraction and relationship mapping.
                        </p>
                        <DomainBuilder
                          onDomainCreated={(domainId) => {
                            alert(`Domain created successfully! ID: ${domainId}`)
                          }}
                        />
                      </div>
                    )}
                  </>
                ) : (
                  <div className="flex items-center justify-center h-full min-h-[400px]">
                    <div className="text-center">
                      <p className="text-gray-400 text-lg mb-2">
                        No analysis yet
                      </p>
                      <p className="text-gray-400 text-sm">
                        Upload a file, enter a URL, or paste text to begin
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
