import { useState } from 'react'
import { ReasoningChainView } from './ReasoningChainView'

export function DetailedView({ results, searchResults = null }) {
  const [activeTab, setActiveTab] = useState('concepts')
  const [selectedItem, setSelectedItem] = useState(null)

  if (!results?.result) return null

  const { concepts, relationships, reasoning_chains, questions } = results.result

  const ConceptCard = ({ concept, index }) => (
    <div
      className="p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => setSelectedItem({ type: 'concept', data: concept })}
    >
      <div className="flex justify-between items-start mb-2">
        <h4 className="font-semibold text-gray-900">{concept.text}</h4>
        <span className="text-xs px-2 py-1 bg-indigo-100 text-indigo-700 rounded">
          {concept.type}
        </span>
      </div>
      <div className="flex items-center gap-4 text-sm text-gray-600">
        <span>Confidence: {(concept.confidence * 100).toFixed(1)}%</span>
      </div>
    </div>
  )

  const RelationshipCard = ({ relationship, index }) => (
    <div
      className="p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => setSelectedItem({ type: 'relationship', data: relationship })}
    >
      <div className="flex items-center gap-2">
        <span className="font-medium text-gray-900">{relationship.source.text}</span>
        <span className="text-indigo-600 font-semibold">→</span>
        <span className="font-medium text-gray-900">{relationship.target.text}</span>
      </div>
      <div className="mt-2">
        <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">
          {relationship.type}
        </span>
      </div>
    </div>
  )

  const ChainCard = ({ chain, index }) => (
    <div
      className="p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => setSelectedItem({ type: 'chain', data: chain })}
    >
      <div className="flex justify-between items-start mb-2">
        <h4 className="font-semibold text-gray-900 capitalize">{chain.type}</h4>
        <span className="text-xs text-gray-500">{chain.steps?.length || 0} steps</span>
      </div>
      <div className="space-y-1 text-sm text-gray-600">
        {chain.steps?.slice(0, 3).map((step, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <span className="text-indigo-600">•</span>
            <span>{step.action}: {step.concept?.text || step.concept}</span>
          </div>
        ))}
        {chain.steps?.length > 3 && (
          <span className="text-xs text-gray-400">+{chain.steps.length - 3} more steps</span>
        )}
      </div>
    </div>
  )

  return (
    <div className="space-y-4">
      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        {[
          { id: 'concepts', label: `Concepts (${concepts?.length || 0})` },
          { id: 'relationships', label: `Relationships (${relationships?.length || 0})` },
          { id: 'chains', label: `Chains (${reasoning_chains?.length || 0})` },
          { id: 'questions', label: `Questions (${questions?.length || 0})` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id)
              setSelectedItem(null)
            }}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === tab.id
                ? 'border-b-2 border-indigo-600 text-indigo-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* List */}
        <div className="lg:col-span-2 space-y-2 max-h-[600px] overflow-y-auto">
        {activeTab === 'concepts' &&
          (() => {
            // Use search results if available, otherwise use all concepts
            const displayConcepts = searchResults?.results?.concepts
              ? searchResults.results.concepts.map(r => ({
                  ...r.item,
                  _searchScore: r.score,
                  _highlights: r.highlights,
                  _matchedFields: r.matched_fields,
                }))
              : concepts

            return displayConcepts?.map((concept, idx) => (
              <ConceptCard key={idx} concept={concept} index={idx} />
            ))}
        {/* Relationships already handled above */}
          {activeTab === 'chains' && (
            <div className="w-full">
              <ReasoningChainView chains={reasoning_chains || []} />
            </div>
          )}
          {activeTab === 'questions' && (
            <div className="space-y-2">
              {questions?.map((q, idx) => (
                <div
                  key={idx}
                  className="p-4 bg-white border border-gray-200 rounded-lg"
                >
                  <p className="text-gray-900">{q}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detail Panel */}
        <div className="lg:col-span-1">
          {selectedItem ? (
            <div className="p-4 bg-white border border-gray-200 rounded-lg sticky top-4">
              <h3 className="font-semibold text-gray-900 mb-4">
                {selectedItem.type.charAt(0).toUpperCase() + selectedItem.type.slice(1)} Details
              </h3>
              <pre className="text-xs bg-gray-50 p-3 rounded overflow-auto max-h-[500px]">
                {JSON.stringify(selectedItem.data, null, 2)}
              </pre>
              <button
                onClick={() => setSelectedItem(null)}
                className="mt-4 w-full text-sm text-indigo-600 hover:text-indigo-700"
              >
                Close
              </button>
            </div>
          ) : (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center text-gray-500">
              Select an item to view details
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
