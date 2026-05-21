import { useEffect } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, BarChart, Bar, Cell
} from 'recharts'
import { useNeoStore } from '../store/neoStore'
import { getNEOOrbit, getNEOMonteCarlo, getNEOHistory } from '../api/neoApi'

const LD_KM = 384402

function StatBox({ label, value, unit, color }) {
  return (
    <div className="detail-stat">
      <div className="detail-stat-label">{label}</div>
      <div className="detail-stat-value" style={{ color: color || 'var(--text-primary)' }}>
        {value ?? '—'} <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{unit}</span>
      </div>
    </div>
  )
}

export function DetailPanel() {
  const {
    selectedNeo, orbitData, monteCarloData, historyData,
    setOrbitData, setMonteCarloData, setHistoryData,
    detailLoading, setDetailLoading,
  } = useNeoStore()

  useEffect(() => {
    if (!selectedNeo) return
    setDetailLoading(true)
    setOrbitData(null)
    setMonteCarloData(null)
    setHistoryData([])

    Promise.allSettled([
      getNEOOrbit(selectedNeo.id).then(setOrbitData),
      getNEOMonteCarlo(selectedNeo.id).then(setMonteCarloData),
      getNEOHistory(selectedNeo.id, 24).then(setHistoryData),
    ]).finally(() => setDetailLoading(false))
  }, [selectedNeo?.id])

  if (!selectedNeo) {
    return (
      <div className="empty-state" style={{ height: '100%' }}>
        <span className="icon">🔭</span>
        <span>Select a NEO to view details</span>
      </div>
    )
  }

  const el = orbitData?.elements

  // Histogram data for Monte Carlo
  const histogramData = monteCarloData?.histogram_km?.map((v, i) => ({ i, km: v })) || []

  return (
    <div className="detail-panel-content">
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <span style={{ fontSize: 14, fontWeight: 700 }}>{selectedNeo.name}</span>
          {selectedNeo.is_potentially_hazardous && <span className="pha-badge">PHA</span>}
          <span className={`tier-badge tier-${selectedNeo.risk_tier || 'LOW'}`}>
            {selectedNeo.risk_tier || '—'}
          </span>
        </div>
        <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          ID: {selectedNeo.id}
          {selectedNeo.designation && ` · ${selectedNeo.designation}`}
        </div>
      </div>

      {/* Stats */}
      <div className="detail-stat-grid">
        <StatBox
          label="Risk Score"
          value={selectedNeo.risk_score?.toFixed(2)}
          color={riskColor(selectedNeo.risk_score)}
        />
        <StatBox
          label="Abs. Magnitude"
          value={selectedNeo.absolute_magnitude?.toFixed(1)}
          unit="H"
        />
        <StatBox
          label="Diameter Min"
          value={selectedNeo.estimated_diameter_min_km?.toFixed(4)}
          unit="km"
        />
        <StatBox
          label="Diameter Max"
          value={selectedNeo.estimated_diameter_max_km?.toFixed(4)}
          unit="km"
        />
        <StatBox
          label="Miss Distance"
          value={selectedNeo.miss_distance_ld?.toFixed(2)}
          unit="LD"
          color="var(--accent-cyan)"
        />
        <StatBox
          label="Velocity"
          value={selectedNeo.relative_velocity_kmps?.toFixed(1)}
          unit="km/s"
        />
      </div>

      {/* Orbital Elements */}
      {detailLoading ? (
        <div className="loading-spinner" style={{ height: 60 }}>
          <div className="spinner" />
        </div>
      ) : el ? (
        <div className="detail-elements">
          <div className="detail-elements-title">Keplerian Elements</div>
          <div className="elements-grid">
            {[
              { label: 'a (AU)', value: el.a?.toFixed(4) },
              { label: 'e', value: el.e?.toFixed(6) },
              { label: 'i (°)', value: el.i?.toFixed(3) },
              { label: 'Ω (°)', value: el.raan?.toFixed(3) },
              { label: 'ω (°)', value: el.argp?.toFixed(3) },
              { label: 'M (°)', value: el.M?.toFixed(3) },
            ].map(item => (
              <div key={item.label} className="element-item">
                <span className="element-label">{item.label}</span>
                <span className="element-value">{item.value ?? '—'}</span>
              </div>
            ))}
          </div>
          {orbitData.closest_approach && (
            <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid var(--border)' }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 4 }}>
                Closest Approach (30-day window)
              </div>
              <div style={{ display: 'flex', gap: 16 }}>
                <div>
                  <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Distance: </span>
                  <span className="element-value">{orbitData.closest_approach.km?.toFixed(0)} km</span>
                </div>
                <div>
                  <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>T+: </span>
                  <span className="element-value">{orbitData.closest_approach.t?.toFixed(1)} days</span>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : null}

      {/* Monte Carlo summary */}
      {monteCarloData && !monteCarloData.error && (
        <div className="detail-elements">
          <div className="detail-elements-title">Monte Carlo Uncertainty (N=500)</div>
          <div className="elements-grid" style={{ gridTemplateColumns: '1fr 1fr 1fr' }}>
            <div className="element-item">
              <span className="element-label">Mean Miss</span>
              <span className="element-value">{(monteCarloData.mean_miss_km / LD_KM).toFixed(3)} LD</span>
            </div>
            <div className="element-item">
              <span className="element-label">± 1σ</span>
              <span className="element-value" style={{ color: 'var(--risk-medium)' }}>
                ±{monteCarloData.std_miss_km?.toFixed(0)} km
              </span>
            </div>
            <div className="element-item">
              <span className="element-label">90% CI</span>
              <span className="element-value" style={{ fontSize: 9 }}>
                {(monteCarloData.p05_miss_km / LD_KM).toFixed(3)}–{(monteCarloData.p95_miss_km / LD_KM).toFixed(3)} LD
              </span>
            </div>
          </div>
          {/* Histogram */}
          {histogramData.length > 0 && (
            <div style={{ height: 60, marginTop: 8 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={histogramData} barSize={4}>
                  <Bar dataKey="km" radius={[2, 2, 0, 0]}>
                    {histogramData.map((entry, i) => (
                      <Cell
                        key={i}
                        fill={entry.km < LD_KM * 5 ? 'var(--risk-high)' : 'var(--accent-blue)'}
                        fillOpacity={0.8}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Historical approach chart */}
      {historyData.length > 0 && (
        <div className="detail-elements">
          <div className="detail-elements-title">Historical Close Approaches</div>
          <div style={{ height: 90 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historyData.slice().reverse()}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="approach_date"
                  tick={{ fontSize: 8, fill: 'var(--text-muted)' }}
                  tickFormatter={v => v.slice(0, 7)}
                  interval="preserveStartEnd"
                />
                <YAxis tick={{ fontSize: 8, fill: 'var(--text-muted)' }} width={30} />
                <Tooltip
                  contentStyle={{
                    background: 'var(--bg-card)', border: '1px solid var(--border)',
                    borderRadius: 8, fontSize: 11, fontFamily: 'var(--font-mono)',
                  }}
                  labelStyle={{ color: 'var(--text-secondary)' }}
                  itemStyle={{ color: 'var(--accent-cyan)' }}
                  formatter={v => [`${v.toFixed(1)} km`, 'Miss Dist']}
                />
                <ReferenceLine y={LD_KM * 5} stroke="var(--risk-high)" strokeDasharray="4 4" strokeWidth={1} />
                <Line
                  type="monotone"
                  dataKey="miss_distance_km"
                  stroke="var(--accent-cyan)"
                  dot={false}
                  strokeWidth={1.5}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  )
}

function riskColor(score) {
  if (!score && score !== 0) return 'var(--text-primary)'
  if (score >= 75) return 'var(--risk-critical)'
  if (score >= 50) return 'var(--risk-high)'
  if (score >= 25) return 'var(--risk-medium)'
  return 'var(--risk-low)'
}
