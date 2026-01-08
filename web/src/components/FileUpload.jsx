import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import { DomainSelector } from './DomainSelector'

export function FileUpload({ onResults, onError, onStartLoading, loading }) {
  const [selectedFile, setSelectedFile] = useState(null)
  const [domain, setDomain] = useState('generic')

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles && acceptedFiles[0]) {
      setSelectedFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'text/plain': ['.txt'],
      'text/html': ['.html', '.htm'],
      'text/markdown': ['.md'],
    },
  })

  const handleUpload = async () => {
    if (!selectedFile) return

    onStartLoading()

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('domain', domain)

      const response = await axios.post('/api/analyze/file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      const taskId = response.data.task_id

      // Poll for results
      await pollResults(taskId)
    } catch (err) {
      onError(err.response?.data?.detail || err.message || 'Upload failed')
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
      <h3 className="text-xl font-semibold text-gray-900 mb-4">Upload Document</h3>
      
      <DomainSelector value={domain} onChange={setDomain} />

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-indigo-500 bg-indigo-50'
            : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'
        }`}
      >
        <input {...getInputProps()} />
        {selectedFile ? (
          <div className="space-y-2">
            <p className="text-green-600 font-medium">✓ {selectedFile.name}</p>
            <p className="text-sm text-gray-500">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-gray-600">
              {isDragActive
                ? 'Drop the file here...'
                : 'Drag & drop a file here, or click to select'}
            </p>
            <p className="text-sm text-gray-400">
              Supports: PDF, DOCX, TXT, HTML, Markdown
            </p>
          </div>
        )}
      </div>

      {selectedFile && (
        <button
          onClick={handleUpload}
          disabled={loading}
          className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Processing...' : 'Analyze Document'}
        </button>
      )}
    </div>
  )
}
