import { useState } from 'react'
import axios from 'axios'
import { DomainSelector } from './DomainSelector'
import { ProgressBar } from './ProgressBar'

export function URLInput({ onResults, onError, onStartLoading, loading }) {
  const [url, setUrl] = useState('')
  const [domain, setDomain] = useState('generic')
  const [useLLM, setUseLLM] = useState(false)
  const [taskId, setTaskId] = useState(null)
  const [showProgress, setShowProgress] = useState(false)

  const handleAnalyze = async () => {
    if (!url.trim()) {
      onError('Please enter a URL')
      return
    }

    onStartLoading()

    try {
      const response = await axios.post('/api/analyze/url', {
        url: url.trim(),
        domain: domain,
        use_llm: useLLM,
      })

      const newTaskId = response.data.task_id
      setTaskId(newTaskId)
      setShowProgress(true)

      // Poll for results (fallback if SSE doesn't work)
      await pollResults(newTaskId)
    } catch (err) {
      onError(err.response?.data?.detail || err.message || 'URL analysis failed')
      setShowProgress(false)
    }
  }

  const handleProgressComplete = (data) => {
    setShowProgress(false)
    onResults(data)
  }

  const handleProgressError = (err) => {
    setShowProgress(false)
    onError(err)
  }

  const pollResults = async (taskId) => {
    const maxAttempts = 60
    let attempts = 0

    const poll = async () => {
      try {
        const response = await axios.get(`/api/results/${taskId}`)
        const data = response.data

        if (data.status === 'completed') {
          onResults(data)
          return
        }

        if (data.status === 'error') {
          onError(data.error || 'Analysis failed')
          return
        }

        // Still processing
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000) // Poll every 2 seconds
        } else {
          onError('Analysis timed out')
        }
      } catch (err) {
        onError(err.response?.data?.detail || err.message || 'Failed to get results')
      }
    }

    poll()
  }

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-semibold text-gray-900 mb-4">Analyze Website</h3>
      
      <DomainSelector value={domain} onChange={setDomain} />
      
      {/* LLM Toggle */}
      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Use LLM Enhancement
          </label>
          <p className="text-xs text-gray-500 mt-1">
            Enable AI-powered concept extraction and relationship inference
          </p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={useLLM}
            onChange={(e) => setUseLLM(e.target.checked)}
            className="sr-only peer"
            disabled={loading}
          />
          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
        </label>
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Website URL
        </label>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/article"
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          disabled={loading}
        />
      </div>

      <button
        onClick={handleAnalyze}
        disabled={loading || !url.trim() || showProgress}
        className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {loading || showProgress ? 'Processing...' : 'Analyze Website'}
      </button>

      {/* Progress Bar */}
      {showProgress && taskId && (
        <div className="mt-4">
          <ProgressBar
            taskId={taskId}
            onComplete={handleProgressComplete}
            onError={handleProgressError}
          />
        </div>
      )}
    </div>
  )
}
