import { useState } from 'react'
import axios from 'axios'
import { DomainSelector } from './DomainSelector'

export function TextInput({ onResults, onError, onStartLoading, loading }) {
  const [text, setText] = useState('')
  const [domain, setDomain] = useState('generic')

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
      })

      onResults(response.data)
    } catch (err) {
      onError(err.response?.data?.detail || err.message || 'Text analysis failed')
    }
  }

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-semibold text-gray-900 mb-4">Analyze Text</h3>
      
      <DomainSelector value={domain} onChange={setDomain} />

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
        disabled={loading || !text.trim()}
        className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? 'Processing...' : 'Analyze Text'}
      </button>
    </div>
  )
}
