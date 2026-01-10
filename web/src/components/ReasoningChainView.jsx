import { useState } from 'react'

export function ReasoningChainView({ chains }) {
  const [selectedChain, setSelectedChain] = useState(null)

  if (!chains || chains.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        No reasoning chains found
      </div>
    )
  }

  const renderChainFlowchart = (chain) => {
    const steps = chain.steps || []
    
    return (
      <div className="space-y-4 p-6 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-lg font-semibold text-gray-900 capitalize">{chain.type}</h4>
          <span className="text-sm text-gray-500">{steps.length} steps</span>
        </div>
        
        <div className="flex flex-col gap-4">
          {steps.map((step, idx) => {
            const concept = step.concept || {}
            const conceptText = typeof concept === 'string' ? concept : concept.text || ''
            const action = step.action || 'analyze'
            
            // Determine step type color
            const actionColors = {
              observe: 'bg-blue-100 border-blue-300 text-blue-800',
              analyze: 'bg-purple-100 border-purple-300 text-purple-800',
              diagnose: 'bg-red-100 border-red-300 text-red-800',
              treat: 'bg-green-100 border-green-300 text-green-800',
              conclude: 'bg-yellow-100 border-yellow-300 text-yellow-800',
              default: 'bg-gray-100 border-gray-300 text-gray-800',
            }
            
            const colorClass = actionColors[action] || actionColors.default
            
            return (
              <div key={idx} className="relative">
                {/* Step Card */}
                <div className={`p-4 border-2 rounded-lg ${colorClass}`}>
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-white border-2 border-current flex items-center justify-center font-bold text-sm">
                      {idx + 1}
                    </div>
                    <div className="flex-1">
                      <div className="font-semibold mb-1 capitalize">{action}</div>
                      <div className="text-sm font-medium mb-2">{conceptText}</div>
                      {step.rationale && (
                        <div className="text-xs italic opacity-75">{step.rationale}</div>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Arrow connector */}
                {idx < steps.length - 1 && (
                  <div className="flex justify-center my-2">
                    <div className="w-0.5 h-6 bg-gray-300"></div>
                    <div className="absolute left-1/2 transform -translate-x-1/2 mt-6">
                      <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Chain List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {chains.map((chain, idx) => (
          <div
            key={idx}
            onClick={() => setSelectedChain(selectedChain === idx ? null : idx)}
            className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
              selectedChain === idx
                ? 'border-indigo-500 bg-indigo-50'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
          >
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-semibold text-gray-900 capitalize">{chain.type || 'Generic'}</h4>
              <span className="text-xs text-gray-500">{chain.steps?.length || 0} steps</span>
            </div>
            <p className="text-sm text-gray-600">
              {chain.steps?.slice(0, 2).map((s, i) => {
                const concept = s.concept || {}
                const text = typeof concept === 'string' ? concept : concept.text || ''
                return `${s.action}: ${text}`
              }).join(' → ')}
              {chain.steps?.length > 2 && ' → ...'}
            </p>
            {chain.confidence && (
              <div className="mt-2">
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-gray-600">Confidence:</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-1.5 max-w-[100px]">
                    <div
                      className="bg-indigo-600 h-1.5 rounded-full"
                      style={{ width: `${chain.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-gray-500">{(chain.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Selected Chain Detail */}
      {selectedChain !== null && chains[selectedChain] && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-xl font-semibold text-gray-900">
              {chains[selectedChain].type || 'Generic'} Chain Details
            </h3>
            <button
              onClick={() => setSelectedChain(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
          {renderChainFlowchart(chains[selectedChain])}
        </div>
      )}
    </div>
  )
}
