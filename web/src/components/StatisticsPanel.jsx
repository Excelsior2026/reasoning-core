export function StatisticsPanel({ results }) {
  if (!results?.result) return null

  const { concepts, relationships, reasoning_chains, questions } = results.result

  // Calculate statistics
  const conceptTypes = {}
  const relationshipTypes = {}
  const avgConfidence = concepts.length > 0
    ? concepts.reduce((sum, c) => sum + (c.confidence || 0), 0) / concepts.length
    : 0

  concepts.forEach((c) => {
    conceptTypes[c.type] = (conceptTypes[c.type] || 0) + 1
  })

  relationships.forEach((r) => {
    relationshipTypes[r.type] = (relationshipTypes[r.type] || 0) + 1
  })

  const chainTypes = {}
  reasoning_chains?.forEach((chain) => {
    chainTypes[chain.type] = (chainTypes[chain.type] || 0) + 1
  })

  return (
    <div className="p-4 bg-white border border-gray-200 rounded-lg space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Statistics</h3>
      
      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-3 rounded-lg">
          <p className="text-2xl font-bold text-blue-600">{concepts?.length || 0}</p>
          <p className="text-sm text-gray-600">Concepts</p>
        </div>
        <div className="bg-green-50 p-3 rounded-lg">
          <p className="text-2xl font-bold text-green-600">{relationships?.length || 0}</p>
          <p className="text-sm text-gray-600">Relationships</p>
        </div>
        <div className="bg-purple-50 p-3 rounded-lg">
          <p className="text-2xl font-bold text-purple-600">{reasoning_chains?.length || 0}</p>
          <p className="text-sm text-gray-600">Chains</p>
        </div>
        <div className="bg-yellow-50 p-3 rounded-lg">
          <p className="text-2xl font-bold text-yellow-600">{questions?.length || 0}</p>
          <p className="text-sm text-gray-600">Questions</p>
        </div>
      </div>

      {/* Average Confidence */}
      <div className="bg-gray-50 p-3 rounded-lg">
        <p className="text-sm text-gray-600 mb-1">Average Confidence</p>
        <div className="flex items-center gap-2">
          <div className="flex-1 bg-gray-200 rounded-full h-2">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all"
              style={{ width: `${avgConfidence * 100}%` }}
            />
          </div>
          <span className="text-sm font-semibold text-gray-900">
            {(avgConfidence * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Concept Types Breakdown */}
      {Object.keys(conceptTypes).length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Concept Types</h4>
          <div className="space-y-1">
            {Object.entries(conceptTypes)
              .sort((a, b) => b[1] - a[1])
              .map(([type, count]) => (
                <div key={type} className="flex justify-between text-sm">
                  <span className="text-gray-600 capitalize">{type}</span>
                  <span className="font-semibold text-gray-900">{count}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Relationship Types Breakdown */}
      {Object.keys(relationshipTypes).length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Relationship Types</h4>
          <div className="space-y-1">
            {Object.entries(relationshipTypes)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 5)
              .map(([type, count]) => (
                <div key={type} className="flex justify-between text-sm">
                  <span className="text-gray-600">{type}</span>
                  <span className="font-semibold text-gray-900">{count}</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
