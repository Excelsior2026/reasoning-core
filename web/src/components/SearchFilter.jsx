import { useState } from 'react'

export function SearchFilter({ onSearch, onFilterChange, filterOptions }) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState('all')

  const handleSearch = (value) => {
    setSearchTerm(value)
    onSearch(value)
  }

  const handleTypeFilter = (value) => {
    setSelectedType(value)
    onFilterChange({ type: value })
  }

  return (
    <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
      <div className="flex gap-4">
        {/* Search */}
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Search
          </label>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search concepts, relationships..."
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        {/* Type Filter */}
        {filterOptions && (
          <div className="w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Type
            </label>
            <select
              value={selectedType}
              onChange={(e) => handleTypeFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="all">All Types</option>
              {filterOptions.map((type) => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>
    </div>
  )
}
