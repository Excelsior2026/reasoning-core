import { useState, useEffect } from 'react'
import axios from 'axios'

export function DomainBuilder({ onDomainCreated }) {
  const [domainName, setDomainName] = useState('')
  const [description, setDescription] = useState('')
  const [conceptTypes, setConceptTypes] = useState([])
  const [newConceptType, setNewConceptType] = useState('')
  const [patterns, setPatterns] = useState({})
  const [relationships, setRelationships] = useState([])
  const [savedDomains, setSavedDomains] = useState([])
  const [selectedDomain, setSelectedDomain] = useState(null)
  const [testText, setTestText] = useState('')
  const [testResults, setTestResults] = useState(null)
  const [activeTab, setActiveTab] = useState('create')

  useEffect(() => {
    loadDomains()
  }, [])

  const loadDomains = async () => {
    try {
      const response = await axios.get('/api/domains')
      setSavedDomains(response.data.domains || [])
    } catch (err) {
      console.error('Failed to load domains:', err)
    }
  }

  const handleAddConceptType = () => {
    if (newConceptType.trim() && !conceptTypes.includes(newConceptType.trim())) {
      setConceptTypes([...conceptTypes, newConceptType.trim()])
      setNewConceptType('')
      if (!patterns[newConceptType.trim()]) {
        setPatterns({ ...patterns, [newConceptType.trim()]: [] })
      }
    }
  }

  const handleRemoveConceptType = (type) => {
    setConceptTypes(conceptTypes.filter(t => t !== type))
    const newPatterns = { ...patterns }
    delete newPatterns[type]
    setPatterns(newPatterns)
  }

  const handleAddPattern = (conceptType, pattern) => {
    if (pattern.trim()) {
      setPatterns({
        ...patterns,
        [conceptType]: [...(patterns[conceptType] || []), pattern.trim()],
      })
    }
  }

  const handleRemovePattern = (conceptType, patternIndex) => {
    setPatterns({
      ...patterns,
      [conceptType]: patterns[conceptType].filter((_, i) => i !== patternIndex),
    })
  }

  const handleSaveDomain = async () => {
    if (!domainName.trim()) {
      alert('Please enter a domain name')
      return
    }

    if (conceptTypes.length === 0) {
      alert('Please add at least one concept type')
      return
    }

    try {
      const config = {
        name: domainName,
        description: description,
        concept_types: conceptTypes,
        concept_patterns: patterns,
        relationship_patterns: relationships,
        rules: [],
      }

      const response = await axios.post('/api/domains', config)
      
      alert('Domain saved successfully!')
      await loadDomains()
      
      if (onDomainCreated) {
        onDomainCreated(response.data.id)
      }

      // Reset form
      setDomainName('')
      setDescription('')
      setConceptTypes([])
      setPatterns({})
      setRelationships([])
    } catch (err) {
      alert('Failed to save domain: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleLoadDomain = async (domainId) => {
    try {
      const response = await axios.get(`/api/domains/${domainId}`)
      const domain = response.data.domain
      
      setDomainName(domain.name)
      setDescription(domain.description || '')
      setConceptTypes(domain.concept_types || [])
      setPatterns(domain.concept_patterns || {})
      setRelationships(domain.relationship_patterns || [])
      setSelectedDomain(domainId)
      setActiveTab('create')
    } catch (err) {
      alert('Failed to load domain: ' + err.message)
    }
  }

  const handleDeleteDomain = async (domainId) => {
    if (!confirm('Are you sure you want to delete this domain?')) {
      return
    }

    try {
      await axios.delete(`/api/domains/${domainId}`)
      await loadDomains()
      if (selectedDomain === domainId) {
        setSelectedDomain(null)
      }
    } catch (err) {
      alert('Failed to delete domain: ' + err.message)
    }
  }

  const handleTestDomain = async () => {
    if (!selectedDomain || !testText.trim()) {
      alert('Please select a domain and enter test text')
      return
    }

    try {
      const response = await axios.post(`/api/domains/${selectedDomain}/test`, null, {
        params: { test_text: testText },
      })
      setTestResults(response.data)
    } catch (err) {
      alert('Test failed: ' + err.message)
    }
  }

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('create')}
          className={`px-6 py-2 font-medium transition-colors ${
            activeTab === 'create'
              ? 'border-b-2 border-indigo-600 text-indigo-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Create Domain
        </button>
        <button
          onClick={() => setActiveTab('browse')}
          className={`px-6 py-2 font-medium transition-colors ${
            activeTab === 'browse'
              ? 'border-b-2 border-indigo-600 text-indigo-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Browse Domains ({savedDomains.length})
        </button>
        <button
          onClick={() => setActiveTab('test')}
          className={`px-6 py-2 font-medium transition-colors ${
            activeTab === 'test'
              ? 'border-b-2 border-indigo-600 text-indigo-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Test Domain
        </button>
      </div>

      {/* Create Tab */}
      {activeTab === 'create' && (
        <div className="space-y-6">
          {/* Basic Info */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Domain Name *
                </label>
                <input
                  type="text"
                  value={domainName}
                  onChange={(e) => setDomainName(e.target.value)}
                  placeholder="e.g., Legal Domain, Scientific Domain"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe what this domain is for..."
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Concept Types */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Concept Types</h3>
            <div className="space-y-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newConceptType}
                  onChange={(e) => setNewConceptType(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddConceptType()}
                  placeholder="Enter concept type (e.g., 'case', 'lawyer', 'court')"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  onClick={handleAddConceptType}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                >
                  Add Type
                </button>
              </div>

              <div className="space-y-2">
                {conceptTypes.map((type, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="font-medium text-gray-900">{type}</span>
                    <button
                      onClick={() => handleRemoveConceptType(type)}
                      className="text-red-600 hover:text-red-700 text-sm"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Patterns */}
          {conceptTypes.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Extraction Patterns</h3>
              <div className="space-y-4">
                {conceptTypes.map((type) => (
                  <div key={type} className="border border-gray-200 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">{type} Patterns</h4>
                    <div className="space-y-2">
                      <PatternEditor
                        patterns={patterns[type] || []}
                        onAdd={(pattern) => handleAddPattern(type, pattern)}
                        onRemove={(index) => handleRemovePattern(type, index)}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Save Button */}
          <button
            onClick={handleSaveDomain}
            className="w-full px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 font-medium"
          >
            Save Domain
          </button>
        </div>
      )}

      {/* Browse Tab */}
      {activeTab === 'browse' && (
        <div className="space-y-4">
          {savedDomains.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No custom domains saved yet
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {savedDomains.map((domain) => (
                <div
                  key={domain.id}
                  className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-semibold text-gray-900">{domain.name}</h4>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleLoadDomain(domain.id)}
                        className="text-indigo-600 hover:text-indigo-700 text-sm"
                      >
                        Load
                      </button>
                      <button
                        onClick={() => handleDeleteDomain(domain.id)}
                        className="text-red-600 hover:text-red-700 text-sm"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{domain.description}</p>
                  <div className="text-xs text-gray-500">
                    {domain.concept_types} concept types
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Test Tab */}
      {activeTab === 'test' && (
        <div className="space-y-4">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Domain</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Domain
                </label>
                <select
                  value={selectedDomain || ''}
                  onChange={(e) => setSelectedDomain(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select a domain...</option>
                  {savedDomains.map((domain) => (
                    <option key={domain.id} value={domain.id}>
                      {domain.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Test Text
                </label>
                <textarea
                  value={testText}
                  onChange={(e) => setTestText(e.target.value)}
                  placeholder="Enter sample text to test the domain..."
                  rows={6}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <button
                onClick={handleTestDomain}
                disabled={!selectedDomain || !testText.trim()}
                className="w-full px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                Test Domain
              </button>
            </div>
          </div>

          {/* Test Results */}
          {testResults && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Results</h3>
              <div className="space-y-2">
                <div>
                  <strong>Concepts Found:</strong> {testResults.result?.concepts?.length || 0}
                </div>
                <div>
                  <strong>Relationships Found:</strong> {testResults.result?.relationships?.length || 0}
                </div>
                {testResults.result?.concepts && testResults.result.concepts.length > 0 && (
                  <div className="mt-4">
                    <h4 className="font-medium mb-2">Concepts:</h4>
                    <div className="space-y-1 max-h-60 overflow-y-auto">
                      {testResults.result.concepts.slice(0, 10).map((c, i) => (
                        <div key={i} className="text-sm p-2 bg-gray-50 rounded">
                          <span className="font-medium">{c.text}</span> ({c.type})
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function PatternEditor({ patterns, onAdd, onRemove }) {
  const [newPattern, setNewPattern] = useState('')

  const handleAdd = () => {
    if (newPattern.trim()) {
      onAdd(newPattern)
      setNewPattern('')
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          type="text"
          value={newPattern}
          onChange={(e) => setNewPattern(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleAdd()}
          placeholder="Enter regex pattern (e.g., '\\b(case|lawsuit)\\b')"
          className="flex-1 px-3 py-1 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
        />
        <button
          onClick={handleAdd}
          className="px-3 py-1 text-sm bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          Add
        </button>
      </div>
      <div className="space-y-1">
        {patterns.map((pattern, idx) => (
          <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
            <code className="text-gray-700">{pattern}</code>
            <button
              onClick={() => onRemove(idx)}
              className="text-red-600 hover:text-red-700 text-xs"
            >
              ×
            </button>
          </div>
        ))}
      </div>
      {patterns.length === 0 && (
        <p className="text-xs text-gray-500 italic">No patterns defined. Domain will use default extraction.</p>
      )}
    </div>
  )
}
