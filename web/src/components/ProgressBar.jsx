import { useEffect, useRef, useState } from 'react'
import { createTaskStream } from '../taskProgress'

export function ProgressBar({ taskId, onComplete, onError }) {
  const [progress, setProgress] = useState(0)
  const [stage, setStage] = useState('initializing')
  const [message, setMessage] = useState('Starting...')
  const onCompleteRef = useRef(onComplete)
  const onErrorRef = useRef(onError)

  useEffect(() => {
    onCompleteRef.current = onComplete
  }, [onComplete])

  useEffect(() => {
    onErrorRef.current = onError
  }, [onError])

  // taskId is the only dependency: stream lifecycle must not restart when
  // progress state or parent-provided callback identities change.
  useEffect(() => {
    if (!taskId) return undefined

    setProgress(0)
    setStage('initializing')
    setMessage('Starting...')

    const stream = createTaskStream({
      taskId,
      onProgress: (next) => {
        setProgress(next.progress)
        setStage(next.stage)
        setMessage(next.message)
      },
      onComplete: (data) => {
        onCompleteRef.current?.(data)
      },
      onError: (err) => {
        onErrorRef.current?.(err)
      },
    })

    return () => stream.dispose()
  }, [taskId])

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
