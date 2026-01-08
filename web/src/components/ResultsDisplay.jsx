export function ResultsDisplay({ results }) {
  if (!results || !results.result) {
    return <p className="text-gray-500">No results to display</p>
  }

  const { result } = results
  const concepts = result.concepts || []
  const relationships = result.relationships || []
  const chains = result.reasoning_chains || []
  const questions = result.questions || []

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <p className="text-2xl font-bold text-blue-600">{concepts.length}</p>
          <p className="text-sm text-gray-600">Concepts</p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <p className="text-2xl font-bold text-green-600">{relationships.length}</p>
          <p className="text-sm text-gray-600">Relationships</p>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <p className="text-2xl font-bold text-purple-600">{chains.length}</p>
          <p className="text-sm text-gray-600">Reasoning Chains</p>
        </div>
      </div>

      {/* Concepts */}
      {concepts.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-900 mb-2">Key Concepts</h4>
          <div className="max-h-48 overflow-y-auto space-y-2">
            {concepts.slice(0, 10).map((concept, idx) => (
              <div key={idx} className="bg-gray-50 p-2 rounded text-sm">
                <span className="font-medium text-gray-900">{concept.text}</span>
                <span className="text-gray-500 ml-2">({concept.type})</span>
                <span className="text-gray-400 ml-2">
                  {(concept.confidence * 100).toFixed(0)}%
                </span>
              </div>
            ))}
            {concepts.length > 10 && (
              <p className="text-xs text-gray-500">
                +{concepts.length - 10} more concepts
              </p>
            )}
          </div>
        </div>
      )}

      {/* Questions */}
      {questions.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-900 mb-2">Generated Questions</h4>
          <ul className="space-y-1 list-disc list-inside text-sm text-gray-700">
            {questions.map((q, idx) => (
              <li key={idx}>{q}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Source Info */}
      {result.source && (
        <div className="bg-gray-50 p-3 rounded text-xs text-gray-600">
          <p className="font-medium mb-1">Source:</p>
          <p>Type: {result.source.type}</p>
          {result.source.filename && <p>File: {result.source.filename}</p>}
          {result.source.url && <p>URL: {result.source.url}</p>}
        </div>
      )}
    </div>
  )
}
