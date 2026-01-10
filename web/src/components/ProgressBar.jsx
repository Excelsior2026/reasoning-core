import { useState, useEffect } from 'react'
import axios from 'axios'

export function ProgressBar({ taskId, onComplete, onError }) {
  const [progress, setProgress] = useState(0)
  const [stage, setStage] = useState('initializing')
  const [message, setMessage] = useState('Starting...')

  useEffect(() => {
    if (!taskId) return

    const eventSource = new EventSource(`/api/progress/${taskId}`)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setProgress(data.progress || 0)
        setStage(data.stage || 'processing')
        setMessage(data.message || '')

        // Handle completion
        if (data.done || data.progress >= 100 || data.status === 'completed') {
          eventSource.close()
          if (onComplete) {
            // Fetch final results
            setTimeout(() => {
              axios.get(`/api/results/${taskId}`).then((response) => {
                if (response.data.status === 'completed') {
                  onComplete(response.data)
                } else if (response.data.status === 'error') {
                  onError(response.data.error || 'Analysis failed')
                }
              }).catch((err) => {
                onError(err.message || 'Failed to get results')
              })
            }, 500)
          }
        }

        // Handle errors
        if (data.status === 'error' || stage === 'error') {
          eventSource.close()
          if (onError) {
            onError(data.error || data.message || 'Analysis failed')
          }
        }
      } catch (err) {
        console.error('Error parsing progress:', err)
      }
    }

    eventSource.onerror = (err) => {
      console.error('SSE error:', err)
      eventSource.close()
      // Fallback to polling if SSE fails
      pollProgress()
    }

    // Fallback polling function
    const pollProgress = async () => {
      const maxAttempts = 300
      let attempts = 0

      const poll = async () => {
        try {
          const response = await axios.get(`/api/results/${taskId}`)
          const data = response.data

          if (data.status === 'completed') {
            setProgress(100)
            setStage('completed')
            setMessage('Complete!')
            if (onComplete) {
              onComplete(data)
            }
            return
          }

          if (data.status === 'error') {
            setStage('error')
            setMessage(data.error || 'Analysis failed')
            if (onError) {
              onError(data.error || 'Analysis failed')
            }
            return
          }

          // Still processing
          attempts++
          if (attempts < maxAttempts) {
            setTimeout(poll, 2000)
          } else {
            if (onError) {
              onError('Analysis timed out')
            }
          }
        } catch (err) {
          console.error('Polling error:', err)
          if (onError) {
            onError(err.message || 'Failed to get progress')
          }
        }
      }

      poll()
    }

    return () => {
      eventSource.close()
    }
  }, [taskId, onComplete, onError, stage])

  const getStageLabel = (stage) => {
    const labels = {
      initializing: 'Initializing...',
      uploaded: 'File uploaded',
      parsing: 'Parsing document...',
      scraping: 'Scraping website...',
      extracting: 'Extracting concepts...',
      extracting_concepts: 'Extracting concepts...',
      mapping_relationships: 'Mapping relationships...',
      building_chains: 'Building reasoning chains...',
      building_graph: 'Building knowledge graph...',
      completed: 'Complete!',
      error: 'Error',
    }
    return labels[stage] || stage
  }

  const getStageColor = (stage) => {
    if (stage === 'error') return 'bg-red-600'
    if (stage === 'completed') return 'bg-green-600'
    return 'bg-indigo-600'
  }

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center text-sm">
        <span className="font-medium text-gray-700">{getStageLabel(stage)}</span>
        <span className="text-gray-500">{progress}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className={`${getStageColor(stage)} h-2.5 rounded-full transition-all duration-300`}
          style={{ width: `${progress}%` }}
        />
      </div>
      {message && (
        <p className="text-xs text-gray-600 mt-1">{message}</p>
      )}
    </div>
  )
}
