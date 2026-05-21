import axios from 'axios'
import {
  getDemoHistory,
  getDemoMonteCarlo,
  getDemoNEO,
  getDemoNEOs,
  getDemoOrbit,
} from '../data/demoNeos'

/** Empty = same-origin (Docker nginx proxy or Vite dev proxy). Set on Render/static hosts. */
export function getApiRoot() {
  return (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
}

function neosBase() {
  const root = getApiRoot()
  return root ? `${root}/neos` : '/neos'
}

function alertsBase() {
  const root = getApiRoot()
  return root ? `${root}/alerts` : '/alerts'
}

const api = axios.create({
  baseURL: neosBase(),
  timeout: 15000,
})

export const getNEOs = (params = {}) =>
  api.get('', { params }).then(r => ({ ...r.data, demo: false })).catch(() => getDemoNEOs(params))

export const getNEO = (id) =>
  api.get(`/${id}`).then(r => ({ ...r.data, demo: false })).catch(() => getDemoNEO(id))

export const getNEOOrbit = (id) =>
  api.get(`/${id}/orbit`).then(r => r.data).catch(() => getDemoOrbit(id))

export const getNEOMonteCarlo = (id) =>
  api.get(`/${id}/montecarlo`).then(r => r.data).catch(() => getDemoMonteCarlo(id))

export const getNEOHistory = (id, limit = 50) =>
  api.get(`/${id}/history`, { params: { limit } }).then(r => r.data).catch(() => getDemoHistory(id, limit))

export const getAlertLog = (limit = 50) =>
  axios.get(`${alertsBase()}/log`, { params: { limit }, timeout: 15000 }).then(r => r.data).catch(() => [])

// ── WebSocket helper ──────────────────────────────────────────────────────────
export function createAlertSocket(onMessage, onOpen, onClose) {
  const root = getApiRoot()
  let url
  if (root) {
    const u = new URL(`${root}/alerts/ws`)
    u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:'
    url = u.toString()
  } else {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    url = `${protocol}://${window.location.host}/alerts/ws`
  }
  const ws = new WebSocket(url)
  ws.onopen  = onOpen  || (() => {})
  ws.onclose = onClose || (() => {})
  ws.onmessage = (evt) => {
    try { onMessage(JSON.parse(evt.data)) }
    catch { /* ignore */ }
  }
  return ws
}
