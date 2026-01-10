import { useState, useEffect } from 'react'

const STORAGE_KEY = 'reasoning-core-history'

export function HistoryPanel({ onLoadHistory, onSelectHistory }) {
  const [history, setHistory] = useState([])
  const [selectedHistory, setSelectedHistory] = useState(null)

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        // Keep only last 20 items
        const recent = parsed.slice(0, 20)
        setHistory(recent)
      }
    } catch (err) {
      console.error('Failed to load history:', err)
    }
  }

  const saveToHistory = (result) => {
    try {
      const existing = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
      const newItem = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        domain: result.domain || 'generic',
        source: result.result?.source || { type: 'unknown' },
        stats: {
          concepts: result.result?.concepts?.length || 0,
          relationships: result.result?.relationships?.length || 0,
          chains: result.result?.reasoning_chains?.length || 0,
        },
        data: result,
      }
      const updated = [newItem, ...existing].slice(0, 20) // Keep last 20
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
      loadHistory()
    } catch (err) {
      console.error('Failed to save history:', err)
    }
  }

  const deleteHistoryItem = (id) => {
    try {
      const existing = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
      const updated = existing.filter((item) => item.id !== id)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
      loadHistory()
      if (selectedHistory?.id === id) {
        setSelectedHistory(null)
      }
    } catch (err) {
      console.error('Failed to delete history:', err)
    }
  }

  const clearHistory = () => {
    if (window.confirm('Are you sure you want to clear all history?')) {
      localStorage.removeItem(STORAGE_KEY)
      setHistory([])
      setSelectedHistory(null)
    }
  }

  const formatDate = (timestamp) => {
    const date = new Date(timestamp)
    return date.toLocaleString()
  }

  const getSourceLabel = (source) => {
    if (source.filename) return `📄 ${source.filename}`
    if (source.url) return `🌐 ${new URL(source.url).hostname}`
    return `✍️ Text Input`
  }

  // Expose save function to parent on mount
  useEffect(() => {
    if (onLoadHistory) {
      onLoadHistory(saveToHistory)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onLoadHistory]) // Only run when onLoadHistory changes, not on every saveToHistory update

  return (
    <div className="p-4 bg-white border border-gray-200 rounded-lg">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">History</h3>
        {history.length > 0 && (
          <button
            onClick={clearHistory}
            className="text-sm text-red-600 hover:text-red-700"
          >
            Clear All
          </button>
        )}
      </div>

      {history.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          <p>No analysis history yet</p>
          <p className="text-sm mt-2">Your analyses will appear here</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[500px] overflow-y-auto">
          {history.map((item) => (
            <div
              key={item.id}
              className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                selectedHistory?.id === item.id
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
              onClick={() => {
                if (selectedHistory?.id === item.id) {
                  setSelectedHistory(null)
                } else {
                  setSelectedHistory(item)
                }
              }}
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">
                    {getSourceLabel(item.source)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatDate(item.timestamp)}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    deleteHistoryItem(item.id)
                  }}
                  className="text-red-500 hover:text-red-700 ml-2"
                  title="Delete"
                >
                  ×
                </button>
              </div>
              <div className="flex gap-4 text-xs text-gray-600">
                <span>{item.stats.concepts} concepts</span>
                <span>{item.stats.relationships} relationships</span>
                <span>{item.stats.chains} chains</span>
                <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded">
                  {item.domain}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Selected History Details */}
      {selectedHistory && (
        <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="flex justify-between items-start mb-2">
            <h4 className="font-semibold text-gray-900">Analysis Details</h4>
            <button
              onClick={() => setSelectedHistory(null)}
              className="text-sm text-indigo-600 hover:text-indigo-700"
            >
              Close
            </button>
          </div>
          {onSelectHistory && (
            <button
              onClick={() => {
                onSelectHistory(selectedHistory.data)
              }}
              className="mt-2 w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition-colors text-sm"
            >
              Load This Analysis
            </button>
          )}
        </div>
      )}
    </div>
  )
}
