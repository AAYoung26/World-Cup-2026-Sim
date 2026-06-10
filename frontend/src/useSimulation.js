// React hook that drives a simulation over the WebSocket and exposes its state.
//
// Flow: POST /api/simulate -> open the returned ws_url -> stream progress
// messages -> receive the final result. If the socket drops mid-run, we
// reconnect with exponential backoff (the backend is reconnection-safe and will
// replay the final result), and fall back to a REST fetch as a last resort.
import { useCallback, useRef, useState } from 'react'
import { fetchResults, startSimulation, wsUrlFromPath } from './api'

const MAX_RECONNECTS = 4

export function useSimulation() {
  const [status, setStatus] = useState('idle') // idle|connecting|running|complete|error|aborted
  const [progress, setProgress] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [reconnecting, setReconnecting] = useState(false)

  const socketRef = useRef(null)
  const wsPathRef = useRef(null)
  const sessionRef = useRef(null)
  const manualCloseRef = useRef(false)
  const doneRef = useRef(false)
  const reconnectRef = useRef(0)

  const cleanupSocket = () => {
    const s = socketRef.current
    if (s) {
      s.onopen = s.onmessage = s.onerror = s.onclose = null
      try {
        s.close()
      } catch {
        /* ignore */
      }
    }
    socketRef.current = null
  }

  const connect = useCallback((path) => {
    const ws = new WebSocket(wsUrlFromPath(path))
    socketRef.current = ws

    ws.onopen = () => {
      setReconnecting(false)
      reconnectRef.current = 0
    }

    ws.onmessage = (ev) => {
      let msg
      try {
        msg = JSON.parse(ev.data)
      } catch {
        return
      }
      if (msg.type === 'progress') {
        setStatus('running')
        setProgress(msg)
      } else if (msg.type === 'complete') {
        doneRef.current = true
        setResult(msg)
        setProgress({ runs_completed: msg.runs_completed, total_runs: msg.num_runs })
        setStatus('complete')
        cleanupSocket()
      } else if (msg.type === 'error') {
        doneRef.current = true
        setError(msg.message || 'Simulation error')
        setStatus('error')
        cleanupSocket()
      }
    }

    ws.onclose = () => {
      if (doneRef.current || manualCloseRef.current) return
      if (reconnectRef.current < MAX_RECONNECTS) {
        const attempt = ++reconnectRef.current
        setReconnecting(true)
        const delay = 1000 * 2 ** (attempt - 1)
        setTimeout(() => {
          if (!doneRef.current && !manualCloseRef.current) connect(wsPathRef.current)
        }, delay)
      } else {
        // Streaming gave up; try one REST fetch for the final result.
        fetchResults(sessionRef.current)
          .then((data) => {
            if (data && data.teams) {
              setResult(data)
              setProgress({ runs_completed: data.runs_completed, total_runs: data.num_runs })
              setStatus('complete')
            } else {
              setError('Lost connection to the simulation')
              setStatus('error')
            }
          })
          .catch(() => {
            setError('Lost connection to the simulation')
            setStatus('error')
          })
      }
    }
  }, [])

  const run = useCallback(
    async ({ eloWeight, numRuns }) => {
      cleanupSocket()
      manualCloseRef.current = false
      doneRef.current = false
      reconnectRef.current = 0
      setReconnecting(false)
      setError(null)
      setResult(null)
      setProgress(null)
      setStatus('connecting')
      try {
        const session = await startSimulation({ eloWeight, numRuns })
        sessionRef.current = session.session_id
        wsPathRef.current = session.ws_url
        connect(session.ws_url)
      } catch (e) {
        setError(e?.message || 'Failed to start simulation')
        setStatus('error')
      }
    },
    [connect],
  )

  // "Abort" closes the live view. The backend keeps computing in the
  // background, so the result remains retrievable via GET /api/results.
  const abort = useCallback(() => {
    manualCloseRef.current = true
    cleanupSocket()
    setReconnecting(false)
    setStatus('aborted')
  }, [])

  const reset = useCallback(() => {
    manualCloseRef.current = true
    cleanupSocket()
    setStatus('idle')
    setProgress(null)
    setResult(null)
    setError(null)
    setReconnecting(false)
  }, [])

  return { status, progress, result, error, reconnecting, run, abort, reset }
}
