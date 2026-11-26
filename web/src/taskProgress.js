import axios from 'axios'

export const DEFAULT_POLL_INTERVAL_MS = 2000
export const DEFAULT_MAX_POLL_ATTEMPTS = 300
export const DEFAULT_RESULT_FETCH_DELAY_MS = 500

/**
 * Owns the single progress stream for one task.
 *
 * Invariant: for a given createTaskStream() call there is at most one
 * EventSource, at most one pending polling timer, and at most one terminal
 * callback (onComplete or onError). All timers/listeners are released by
 * dispose(). Dependencies are injected so the invariant can be tested without
 * a browser.
 */
export function createTaskStream({
  taskId,
  onProgress = () => {},
  onComplete = () => {},
  onError = () => {},
  EventSourceImpl = globalThis.EventSource,
  getResults = async (id) => (await axios.get(`/api/results/${id}`)).data,
  schedule = (fn, delay) => setTimeout(fn, delay),
  cancel = (handle) => clearTimeout(handle),
  pollIntervalMs = DEFAULT_POLL_INTERVAL_MS,
  maxPollAttempts = DEFAULT_MAX_POLL_ATTEMPTS,
  resultFetchDelayMs = DEFAULT_RESULT_FETCH_DELAY_MS,
}) {
  if (!taskId) {
    return { dispose() {}, inspect: () => ({ disposed: true, streamOpen: false }) }
  }

  if (typeof EventSourceImpl !== 'function') {
    throw new Error('EventSource is unavailable; pass EventSourceImpl')
  }

  let source = null
  let timer = null
  let settled = false
  let finalizing = false
  let polling = false
  let disposed = false

  const cancelTimer = () => {
    if (timer !== null) {
      cancel(timer)
      timer = null
    }
  }

  const closeStream = () => {
    if (source) {
      source.close()
      source = null
    }
  }

  const finish = (callback, payload) => {
    if (settled || disposed) return
    settled = true
    cancelTimer()
    closeStream()
    callback(payload)
  }

  const fail = (message) => finish(onError, message)

  const poll = async (attempts) => {
    if (settled || disposed) return

    try {
      const data = await getResults(taskId)
      if (settled || disposed) return

      if (data.status === 'completed') {
        finish(onComplete, data)
        return
      }
      if (data.status === 'error') {
        fail(data.error || 'Analysis failed')
        return
      }
      if (attempts >= maxPollAttempts) {
        fail('Analysis timed out')
        return
      }

      timer = schedule(() => {
        timer = null
        poll(attempts + 1)
      }, pollIntervalMs)
    } catch (err) {
      if (settled || disposed) return
      fail(err?.message || 'Failed to get progress')
    }
  }

  const startPolling = () => {
    if (settled || disposed || finalizing || polling || timer !== null) return
    polling = true
    poll(0)
  }

  const fetchFinalResults = async () => {
    if (settled || disposed) return

    try {
      const data = await getResults(taskId)
      if (settled || disposed) return

      if (data.status === 'completed') {
        finish(onComplete, data)
      } else if (data.status === 'error') {
        fail(data.error || 'Analysis failed')
      } else {
        fail('Analysis finished without results')
      }
    } catch (err) {
      if (settled || disposed) return
      fail(err?.message || 'Failed to get results')
    }
  }

  const handleCompletion = () => {
    if (settled || disposed || finalizing) return
    finalizing = true
    closeStream()
    timer = schedule(() => {
      timer = null
      fetchFinalResults()
    }, resultFetchDelayMs)
  }

  source = new EventSourceImpl(`/api/progress/${taskId}`)

  source.onmessage = (event) => {
    if (settled || disposed || finalizing) return

    let data
    try {
      data = JSON.parse(event.data)
    } catch (err) {
      console.error('Error parsing progress:', err)
      return
    }

    onProgress({
      progress: typeof data.progress === 'number' ? data.progress : 0,
      stage: data.stage || 'processing',
      message: data.message || '',
    })

    if (data.done || data.progress >= 100 || data.status === 'completed') {
      handleCompletion()
    } else if (data.status === 'error' || data.stage === 'error') {
      fail(data.error || data.message || 'Analysis failed')
    }
  }

  source.onerror = () => {
    if (settled || disposed || finalizing) return
    closeStream()
    startPolling()
  }

  return {
    dispose() {
      if (disposed) return
      disposed = true
      cancelTimer()
      closeStream()
    },
    inspect() {
      return {
        streamOpen: Boolean(source),
        timerPending: timer !== null,
        polling,
        settled,
        finalizing,
        disposed,
      }
    },
  }
}
