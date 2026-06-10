// Thin API layer over the FastAPI backend.
//
// In dev, Vite proxies /api and /ws to the backend (see vite.config.js), so we
// use same-origin relative URLs everywhere.
import axios from 'axios'

const http = axios.create({ baseURL: '/', timeout: 15000 })

export async function fetchTeams() {
  const { data } = await http.get('/api/teams')
  return data
}

export async function fetchHealth() {
  const { data } = await http.get('/api/health')
  return data
}

// Create a simulation session. Returns { session_id, ws_url, elo_weight, num_runs }.
export async function startSimulation({ eloWeight, numRuns }) {
  const { data } = await http.post('/api/simulate', {
    elo_weight: eloWeight,
    num_runs: numRuns,
  })
  return data
}

export async function fetchResults(sessionId) {
  const { data } = await http.get(`/api/results/${sessionId}`)
  return data
}

// Build an absolute ws:// URL from a relative path returned by the backend.
export function wsUrlFromPath(path) {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}${path}`
}
