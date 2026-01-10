import { useState } from 'react'

export function ExportPanel({ data }) {
  const [exportFormat, setExportFormat] = useState('json')

  const exportJSON = () => {
    const dataStr = JSON.stringify(data, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `reasoning-core-export-${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const exportCSV = () => {
    const concepts = data?.result?.concepts || []
    const relationships = data?.result?.relationships || []
    
    // Concepts CSV
    let csv = 'Type,Concept,Type,Confidence\n'
    concepts.forEach((c) => {
      csv += `concept,"${c.text.replace(/"/g, '""')}",${c.type},${c.confidence}\n`
    })
    
    // Relationships CSV
    relationships.forEach((r) => {
      csv += `relationship,"${r.source.text.replace(/"/g, '""')}","${r.target.text.replace(/"/g, '""')}",${r.type}\n`
    })
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `reasoning-core-export-${Date.now()}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  const exportMarkdown = async () => {
    if (!data?.task_id) {
      alert('Task ID not available')
      return
    }
    try {
      const response = await fetch(`/api/export/${data.task_id}/markdown`)
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `reasoning-core-${data.task_id}.md`
      link.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('Failed to export Markdown: ' + err.message)
    }
  }

  const exportPDF = async () => {
    if (!data?.task_id) {
      alert('Task ID not available')
      return
    }
    try {
      const response = await fetch(`/api/export/${data.task_id}/pdf`)
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `reasoning-core-${data.task_id}.pdf`
      link.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('Failed to export PDF: ' + err.message)
    }
  }

  const exportHTML = async () => {
    if (!data?.task_id) {
      alert('Task ID not available')
      return
    }
    try {
      const response = await fetch(`/api/export/${data.task_id}/html`)
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `reasoning-core-${data.task_id}.html`
      link.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('Failed to export HTML: ' + err.message)
    }
  }

  const exportGraphImage = () => {
    // This would export the graph visualization
    // For now, we'll just copy the graph data
    const graphData = data?.result?.knowledge_graph
    if (!graphData) {
      alert('No graph data available to export')
      return
    }
    
    const dataStr = JSON.stringify(graphData, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `reasoning-core-graph-${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const handleExport = () => {
    switch (exportFormat) {
      case 'json':
        exportJSON()
        break
      case 'csv':
        exportCSV()
        break
      case 'markdown':
        exportMarkdown()
        break
      case 'pdf':
        exportPDF()
        break
      case 'html':
        exportHTML()
        break
      case 'graph':
        exportGraphImage()
        break
      default:
        exportJSON()
    }
  }

  if (!data) return null

  return (
    <div className="p-4 bg-white border border-gray-200 rounded-lg">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Data</h3>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Export Format
          </label>
          <select
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="json">JSON (Full Data)</option>
            <option value="csv">CSV (Concepts & Relationships)</option>
            <option value="markdown">Markdown Report</option>
            <option value="pdf">PDF Report</option>
            <option value="html">HTML Report</option>
            <option value="graph">Graph (Knowledge Graph JSON)</option>
          </select>
        </div>
        <button
          onClick={handleExport}
          className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition-colors"
        >
          Export Data
        </button>
      </div>
    </div>
  )
}
