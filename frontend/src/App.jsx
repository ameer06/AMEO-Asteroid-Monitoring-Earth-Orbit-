import { useState, useEffect } from 'react'
import { useNeoStore } from './store/neoStore'
import { OrbitalScene } from './components/OrbitalScene'
import { NEOTable } from './components/NEOTable'
import { RiskLeaderboard } from './components/RiskLeaderboard'
import { DetailPanel } from './components/DetailPanel'
import { AlertBanner } from './components/AlertBanner'
import { TimeScrubber } from './components/TimeScrubber'
import { getNEOOrbit, getNEOs } from './api/neoApi'


function Clock() {
  const [time, setTime] = useState(new Date())
  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  return (
    <span className="topbar-time">
      {time.toUTCString().replace('GMT', 'UTC')}
    </span>
  )
}

export default function App() {
  const {
    neos, selectedNeo, activeTab, setActiveTab, wsConnected,
    hazardousOnly, sortBy, sortDir, page,
    setNeos, setLoading, setError, demoMode, setDemoMode,
  } = useNeoStore()
  const [orbitDataMap, setOrbitDataMap] = useState({})

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    getNEOs({ page, limit: 30, hazardous_only: hazardousOnly, sort_by: sortBy, sort_dir: sortDir })
      .then(data => {
        if (cancelled) return
        setNeos(data.items || [], data.total || 0)
        setDemoMode(Boolean(data.demo))
      })
      .catch(e => {
        if (!cancelled) setError(e.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [page, hazardousOnly, sortBy, sortDir])

  // Pre-fetch orbit data for top 10 NEOs
  useEffect(() => {
    const top10 = neos.slice(0, 10)
    top10.forEach(neo => {
      if (!orbitDataMap[neo.id]) {
        getNEOOrbit(neo.id)
          .then(data => setOrbitDataMap(prev => ({ ...prev, [neo.id]: data })))
          .catch(() => {})
      }
    })
  }, [neos])

  return (
    <div className="app">
      {/* ── Topbar ──────────────────────────────────────────────────────── */}
      <header className="topbar">
        <div className="topbar-logo">
          <div className="topbar-logo-icon">☄</div>
          <h1>AMEO <span>Asteroid Monitoring & Earth Orbit</span></h1>
        </div>

        <div className="topbar-meta">
          <div className={`ws-status ${demoMode ? 'ws-demo' : (wsConnected ? 'ws-connected' : 'ws-disconnected')}`}>
            <div className="ws-dot" />
            {demoMode ? 'Demo' : (wsConnected ? 'Live' : 'Offline')}
          </div>
          <div className="live-badge">
            <div className="live-dot" />
            {demoMode ? 'Sample Feed' : 'NeoWs Feed'}
          </div>
          <Clock />
        </div>
      </header>

      {/* ── Main Content ─────────────────────────────────────────────────── */}
      <main className="main-content">

        {/* ── 3D Orbital Scene (left, spans both rows) ────────────────── */}
        <section className="scene-panel">
          <div className="scene-overlay">
            <div className="scene-badge">3D Orbital Visualization</div>
          </div>
          <div className="orbital-scene-frame">
            <OrbitalScene orbitDataMap={orbitDataMap} />
          </div>
          <TimeScrubber />
        </section>

        {/* ── Right column top: NEO Table or Leaderboard ──────────────── */}
        <section className="panel">
          <div className="panel-header">
            <div style={{ display: 'flex', gap: 4 }}>
              <button
                id="tab-table"
                onClick={() => setActiveTab('table')}
                style={{
                  background: activeTab === 'table' ? 'rgba(79,158,255,0.15)' : 'transparent',
                  border: activeTab === 'table' ? '1px solid var(--accent-blue)' : '1px solid var(--border)',
                  borderRadius: 6, padding: '4px 12px', cursor: 'pointer',
                  color: activeTab === 'table' ? 'var(--accent-blue)' : 'var(--text-muted)',
                  fontSize: 11, fontWeight: 600, letterSpacing: '0.06em',
                  fontFamily: 'var(--font-ui)',
                }}
              >NEO FEED</button>
              <button
                id="tab-risk"
                onClick={() => setActiveTab('risk')}
                style={{
                  background: activeTab === 'risk' ? 'rgba(79,158,255,0.15)' : 'transparent',
                  border: activeTab === 'risk' ? '1px solid var(--accent-blue)' : '1px solid var(--border)',
                  borderRadius: 6, padding: '4px 12px', cursor: 'pointer',
                  color: activeTab === 'risk' ? 'var(--accent-blue)' : 'var(--text-muted)',
                  fontSize: 11, fontWeight: 600, letterSpacing: '0.06em',
                  fontFamily: 'var(--font-ui)',
                }}
              >RISK RANK</button>
            </div>
          </div>
          <div className="panel-body" style={{ padding: 0, display: 'flex', flexDirection: 'column' }}>
            {activeTab === 'table' ? <NEOTable /> : (
              <div style={{ padding: 10, overflow: 'auto' }}>
                <RiskLeaderboard />
              </div>
            )}
          </div>
        </section>

        {/* ── Right column bottom: Detail Panel ───────────────────────── */}
        <section className="panel detail-panel-shell">
          <div className="panel-header">
            <span className="panel-title">
              <span className="icon">🔬</span>
              {selectedNeo ? selectedNeo.name : 'Object Detail'}
            </span>
            {selectedNeo?.nasa_jpl_url && (
              <a
                href={selectedNeo.nasa_jpl_url}
                target="_blank"
                rel="noreferrer"
                style={{ fontSize: 10, color: 'var(--accent-blue)', textDecoration: 'none' }}
              >
                JPL ↗
              </a>
            )}
          </div>
          <div className="panel-body">
            <DetailPanel />
          </div>
        </section>

      </main>

      {/* ── Alert Toast Layer ─────────────────────────────────────────── */}
      <AlertBanner />
    </div>
  )
}
