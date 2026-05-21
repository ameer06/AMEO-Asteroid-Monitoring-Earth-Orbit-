import { useNeoStore } from '../store/neoStore'

const COLS = [
  { key: 'name',                    label: 'Name',           sortable: true,  mobile: true  },
  { key: 'risk_score',              label: 'Risk Score',     sortable: true,  mobile: true  },
  { key: 'risk_tier',               label: 'Tier',           sortable: false, mobile: true  },
  { key: 'estimated_diameter_max_km', label: 'Diam (km)',   sortable: true,  mobile: false },
  { key: 'miss_distance_ld',        label: 'Miss Dist',      sortable: false, mobile: true  },
  { key: 'relative_velocity_kmps',  label: 'Velocity',       sortable: false, mobile: false },
  { key: 'pha',                     label: 'PHA',            sortable: false, mobile: true  },
]

function TierBadge({ tier }) {
  if (!tier) return null
  return <span className={`tier-badge tier-${tier}`}>{tier}</span>
}

export function NEOTable() {
  const {
    neos, total, loading, error,
    selectedNeo, setSelectedNeo,
    hazardousOnly, setHazardousOnly,
    searchQuery, setSearchQuery,
    sortBy, sortDir, setSortBy,
    page, setPage,
  } = useNeoStore()

  const displayed = searchQuery
    ? neos.filter(n => n.name.toLowerCase().includes(searchQuery.toLowerCase()))
    : neos

  if (error) return (
    <div className="empty-state">
      <span className="icon">⚠</span>
      <span>API Error: {error}</span>
      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
        Make sure the backend is running on port 8000
      </span>
    </div>
  )

  return (
    <>
      {/* Filter bar */}
      <div className="filter-bar">
        <input
          id="neo-search"
          className="filter-input"
          placeholder="Search by name…"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />
        <button
          id="filter-pha-toggle"
          className={`filter-toggle ${hazardousOnly ? 'active' : ''}`}
          onClick={() => setHazardousOnly(!hazardousOnly)}
        >
          ☄ PHA Only
        </button>
        <span style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
          {total} objects
        </span>
      </div>

      <p className="neo-table-scroll-hint" aria-hidden="true">Swipe table → for more columns</p>

      {/* Table */}
      <div className="neo-table-wrap">
        {loading ? (
          <div className="loading-spinner" style={{ height: 200 }}>
            <div className="spinner" />
            <span>Fetching NEO data…</span>
          </div>
        ) : (
          <table className="neo-table">
            <thead>
              <tr>
                {COLS.map(col => (
                  <th
                    key={col.key}
                    className={col.mobile ? '' : 'col-hide-mobile'}
                    onClick={() => col.sortable && setSortBy(col.key)}
                    style={{ cursor: col.sortable ? 'pointer' : 'default' }}
                  >
                    {col.label}
                    {col.sortable && sortBy === col.key && (
                      <span style={{ marginLeft: 4 }}>{sortDir === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {displayed.length === 0 ? (
                <tr>
                  <td colSpan={COLS.length} style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>
                    No objects found
                  </td>
                </tr>
              ) : displayed.map(neo => (
                <tr
                  key={neo.id}
                  className={selectedNeo?.id === neo.id ? 'selected' : ''}
                  onClick={() => setSelectedNeo(neo)}
                  id={`neo-row-${neo.id}`}
                >
                  <td className="col-name">
                    <span style={{ fontWeight: 600, fontSize: 12 }}>{neo.name}</span>
                    {neo.designation && (
                      <span className="mono" style={{ marginLeft: 6, color: 'var(--text-muted)', fontSize: 10 }}>
                        {neo.designation}
                      </span>
                    )}
                  </td>
                  <td>
                    <span
                      className="mono"
                      style={{
                        color: riskColor(neo.risk_score),
                        fontWeight: 700,
                        fontSize: 13,
                      }}
                    >
                      {neo.risk_score?.toFixed(1) ?? '—'}
                    </span>
                  </td>
                  <td><TierBadge tier={neo.risk_tier} /></td>
                  <td className="mono col-hide-mobile">
                    {neo.estimated_diameter_max_km != null
                      ? neo.estimated_diameter_max_km.toFixed(3)
                      : '—'}
                  </td>
                  <td className="mono" style={{ color: 'var(--accent-cyan)' }}>
                    {neo.miss_distance_ld != null ? `${neo.miss_distance_ld.toFixed(2)} LD` : '—'}
                  </td>
                  <td className="mono col-hide-mobile">
                    {neo.relative_velocity_kmps != null ? `${neo.relative_velocity_kmps.toFixed(1)} km/s` : '—'}
                  </td>
                  <td>
                    {neo.is_potentially_hazardous && (
                      <span className="pha-badge">PHA</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      <div className="table-pagination">
        <button
          id="page-prev"
          className="scrubber-btn"
          disabled={page <= 1}
          onClick={() => setPage(page - 1)}
          style={{ opacity: page <= 1 ? 0.4 : 1 }}
        >◀</button>
        <span className="mono" style={{ color: 'var(--text-muted)', fontSize: 11, alignSelf: 'center' }}>
          {page} / {Math.max(1, Math.ceil(total / 30))}
        </span>
        <button
          id="page-next"
          className="scrubber-btn"
          disabled={page >= Math.ceil(total / 30)}
          onClick={() => setPage(page + 1)}
          style={{ opacity: page >= Math.ceil(total / 30) ? 0.4 : 1 }}
        >▶</button>
      </div>
    </>
  )
}

function riskColor(score) {
  if (!score) return 'var(--text-muted)'
  if (score >= 75) return 'var(--risk-critical)'
  if (score >= 50) return 'var(--risk-high)'
  if (score >= 25) return 'var(--risk-medium)'
  return 'var(--risk-low)'
}
