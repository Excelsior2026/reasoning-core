import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile, readdir } from 'node:fs/promises'
import { createTaskStream } from '../src/taskProgress.js'

const flush = () => new Promise((resolve) => setImmediate(resolve))

class FakeEventSource {
  static instances = []

  constructor(url) {
    this.url = url
    this.closed = false
    this.onmessage = null
    this.onerror = null
    FakeEventSource.instances.push(this)
  }

  emit(payload) {
    this.onmessage?.({ data: JSON.stringify(payload) })
  }

  fail() {
    this.onerror?.({})
  }

  close() {
    this.closed = true
  }
}

function timerHarness() {
  const timers = []
  let nextId = 1

  return {
    schedule(fn, delay) {
      const id = nextId++
      timers.push({ id, fn, delay, cancelled: false, fired: false })
      return id
    },
    cancel(id) {
      const timer = timers.find((candidate) => candidate.id === id)
      if (timer) timer.cancelled = true
    },
    pending() {
      return timers.filter((timer) => !timer.cancelled && !timer.fired)
    },
    runNext() {
      const timer = timers.find((candidate) => !candidate.cancelled && !candidate.fired)
      if (!timer) return false
      timer.fired = true
      timer.fn()
      return true
    },
  }
}

function makeStream(overrides = {}) {
  FakeEventSource.instances = []
  const timers = timerHarness()
  const events = { progress: [], complete: [], error: [], results: 0 }

  const stream = createTaskStream({
    taskId: 'task-1',
    EventSourceImpl: FakeEventSource,
    schedule: timers.schedule,
    cancel: timers.cancel,
    getResults: async () => {
      events.results++
      return { status: 'processing' }
    },
    onProgress: (next) => events.progress.push(next),
    onComplete: (data) => events.complete.push(data),
    onError: (message) => events.error.push(message),
    ...overrides,
  })

  return { stream, timers, events, source: FakeEventSource.instances[0] }
}

test('one EventSource per task; duplicate completion messages deliver one result', async () => {
  const { stream, timers, events, source } = makeStream({
    resultFetchDelayMs: 500,
    getResults: async () => {
      events.results++
      return { status: 'completed', result: { concepts: [] } }
    },
  })

  assert.equal(FakeEventSource.instances.length, 1)
  assert.equal(source.url, '/api/progress/task-1')

  source.emit({ progress: 10, stage: 'parsing', message: 'Reading' })
  source.emit({ progress: 50, stage: 'extracting', message: 'Extracting' })
  source.emit({ progress: 100, status: 'completed', message: 'Done' })
  source.emit({ progress: 100, status: 'completed', message: 'Done again' })

  assert.equal(events.progress.length, 3, 'messages after completion are ignored')
  assert.equal(FakeEventSource.instances.length, 1, 'never reopens a stream')
  assert.equal(timers.pending().length, 1, 'one delayed final fetch')
  assert.equal(events.results, 0)

  timers.runNext()
  await flush()

  assert.equal(events.results, 1)
  assert.equal(events.complete.length, 1)
  assert.equal(events.error.length, 0)
  assert.equal(source.closed, true)
  assert.deepEqual(stream.inspect(), {
    streamOpen: false,
    timerPending: false,
    polling: false,
    settled: true,
    finalizing: true,
    disposed: false,
  })

  stream.dispose()
})

test('SSE failure starts exactly one polling chain and emits one terminal error', async () => {
  const { stream, events, source } = makeStream({
    getResults: async () => {
      events.results++
      return { status: 'error', error: 'boom' }
    },
  })

  source.fail()
  source.fail()
  await flush()

  assert.equal(FakeEventSource.instances.length, 1)
  assert.equal(events.results, 1, 'second error event must not start a second poll')
  assert.deepEqual(events.error, ['boom'])
  assert.equal(events.complete.length, 0)
  assert.equal(source.closed, true)

  stream.dispose()
})

test('dispose closes the stream and cancels pending polling timers', async () => {
  const { stream, timers, events, source } = makeStream()

  source.fail()
  await flush()
  assert.equal(timers.pending().length, 1)

  stream.dispose()

  assert.equal(source.closed, true)
  assert.equal(timers.pending().length, 0)
  assert.equal(timers.runNext(), false)
  assert.deepEqual(events.error, [])
  assert.equal(stream.inspect().disposed, true)
})

test('source invariant: one SSE site, no FileUpload polling, stable ProgressBar deps', async () => {
  const srcDir = new URL('../src/', import.meta.url)
  const paths = (await readdir(srcDir, { recursive: true }))
    .filter((path) => /\.(js|jsx)$/.test(path))
    .map((path) => path.replace(/\\/g, '/'))

  const eventSourcePaths = []
  let fileUpload = ''
  let progressBar = ''

  for (const path of paths) {
    const text = await readFile(new URL(path, srcDir), 'utf8')
    if (/new EventSource/.test(text)) eventSourcePaths.push(path)
    if (path.endsWith('components/FileUpload.jsx')) fileUpload = text
    if (path.endsWith('components/ProgressBar.jsx')) progressBar = text
  }

  assert.deepEqual(eventSourcePaths, ['taskProgress.js'])
  assert.doesNotMatch(fileUpload, /pollResults|setTimeout|setInterval/)
  assert.match(progressBar, /return \(\) => stream\.dispose\(\)\n  \}, \[taskId\]\)/)
  assert.doesNotMatch(
    progressBar,
    /stream\.dispose\(\)\n  \}, \[[^\]]*(stage|onComplete|onError)/
  )
})
