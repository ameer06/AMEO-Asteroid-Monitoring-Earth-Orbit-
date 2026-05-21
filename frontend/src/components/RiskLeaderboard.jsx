import { useNeoStore } from '../store/neoStore'

function riskColor(score) {
  if (!score && score !== 0) return 'var(--text-muted)'
  if (score >= 75) return 'var(--risk-critical)'
  if (score >= 50) return 'var(--risk-high)'
  if (score >= 25) return 'var(--risk-medium)'
  return 'var(--risk-low)'
}

export function RiskLeaderboard() {
  const { neos, selectedNeo, setSelectedNeo } = useNeoStore()

  const sorted = [...neos]
    .sort((a, b) => (b.risk_score ?? 0) - (a.risk_score ?? 0))
    .slice(0, 8)

  if (!sorted.length) {
    return (
      <div className="empty-state">
        <span className="icon">📊</span>
        <span>No data yet</span>
      </div>
    )
  }

  return (
    <div className="leaderboard-list">
      {sorted.map((neo, idx) => {
        const score = neo.risk_score ?? 0
        const color = riskColor(score)
        const isSelected = selectedNeo?.id === neo.id
        return (
          <div
            key={neo.id}
            id={`lb-item-${neo.id}`}
            className={`leaderboard-item ${isSelected ? 'selected' : ''}`}
            onClick={() => setSelectedNeo(neo)}
          >
            <div className="lb-row">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: 10,
                  color: 'var(--text-muted)', minWidth: 14
                }}>
                  #{idx + 1}
                </span>
                <span className="lb-name">{neo.name}</span>
                {neo.is_potentially_hazardous && (
                  <span className="pha-badge">PHA</span>
                )}
              </div>
              <div style={{ display: 'flex', align: 'center', gap: 6 }}>
                <span className={`tier-badge tier-${neo.risk_tier || 'LOW'}`}>
                  {neo.risk_tier || 'LOW'}
                </span>
                <span className="lb-score" style={{ color }}>{score.toFixed(1)}</span>
              </div>
            </div>

            {/* Score bar */}
            <div className="score-bar-track">
              <div
                className="score-bar-fill"
                style={{ width: `${score}%`, background: color }}
              />
            </div>

            {/* Diameter */}
            <div style={{ marginTop: 5, display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                Ø {neo.estimated_diameter_max_km?.toFixed(3) ?? '?'} km
              </span>
              <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                {neo.absolute_magnitude != null ? `H=${neo.absolute_magnitude.toFixed(1)}` : ''}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
