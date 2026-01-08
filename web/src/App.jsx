import { useState } from 'react'
import { FileUpload } from './components/FileUpload'
import { URLInput } from './components/URLInput'
import { TextInput } from './components/TextInput'
import { ResultsDisplay } from './components/ResultsDisplay'
import { KnowledgeGraphViewer } from './components/KnowledgeGraphViewer'

function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('file') // 'file', 'url', 'text'

  const handleResults = (data) => {
    setResults(data)
    setLoading(false)
    setError(null)
  }

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            🧠 Reasoning Core
          </h1>
          <p className="text-gray-600 text-lg">
            Transform documents, websites, and text into intelligent knowledge graphs
          </p>
        </header>

        {/* Tabs */}
        <div className="mb-6 flex justify-center">
          <div className="inline-flex rounded-lg bg-white p-1 shadow-md">
            <button
              onClick={() => setActiveTab('file')}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                activeTab === 'file'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              📄 Upload File
            </button>
            <button
              onClick={() => setActiveTab('url')}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                activeTab === 'url'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              🌐 Website URL
            </button>
            <button
              onClick={() => setActiveTab('text')}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                activeTab === 'text'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              ✍️ Paste Text
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Panel */}
            <div className="bg-white rounded-lg shadow-lg p-6">
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
            </div>

            {/* Results Panel */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              {results ? (
                <div className="space-y-4">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">
                    Analysis Results
                  </h2>
                  <ResultsDisplay results={results} />
                </div>
              ) : (
                <div className="flex items-center justify-center h-full min-h-[400px]">
                  <p className="text-gray-400 text-center">
                    Upload a file, enter a URL, or paste text to begin analysis
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Knowledge Graph Viewer - Full Width */}
          {results?.result?.knowledge_graph && (
            <div className="mt-6 bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Knowledge Graph Visualization
              </h2>
              <KnowledgeGraphViewer graph={results.result.knowledge_graph} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
