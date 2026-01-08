import { useState } from 'react'
import axios from 'axios'
import { DomainSelector } from './DomainSelector'

export function URLInput({ onResults, onError, onStartLoading, loading }) {
  const [url, setUrl] = useState('')
  const [domain, setDomain] = useState('generic')

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
      })

      const taskId = response.data.task_id

      // Poll for results
      await pollResults(taskId)
    } catch (err) {
      onError(err.response?.data?.detail || err.message || 'URL analysis failed')
    }
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
        disabled={loading || !url.trim()}
        className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? 'Processing...' : 'Analyze Website'}
      </button>
    </div>
  )
}
