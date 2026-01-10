import { useState } from 'react'
import axios from 'axios'
import { DomainSelector } from './DomainSelector'
import { ProgressBar } from './ProgressBar'

export function TextInput({ onResults, onError, onStartLoading, loading }) {
  const [text, setText] = useState('')
  const [domain, setDomain] = useState('generic')
  const [useLLM, setUseLLM] = useState(false)
  const [taskId, setTaskId] = useState(null)
  const [showProgress, setShowProgress] = useState(false)

  const handleAnalyze = async () => {
    if (!text.trim()) {
      onError('Please enter some text')
      return
    }

    onStartLoading()

    try {
      const response = await axios.post('/api/analyze/text', {
        text: text.trim(),
        domain: domain,
        use_llm: useLLM,
      })

      // Text analysis is synchronous, so task_id may not be present
      if (response.data.task_id) {
        setTaskId(response.data.task_id)
        setShowProgress(true)
      } else {
        // Direct response (synchronous)
        onResults(response.data)
      }
    } catch (err) {
      onError(err.response?.data?.detail || err.message || 'Text analysis failed')
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

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-semibold text-gray-900 mb-4">Analyze Text</h3>
      
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
          Text to Analyze
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste or type your text here..."
          rows={10}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm"
          disabled={loading}
        />
      </div>

      <button
        onClick={handleAnalyze}
        disabled={loading || !text.trim() || showProgress}
        className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {loading || showProgress ? 'Processing...' : 'Analyze Text'}
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
