const DEMO_ELEMENTS = {
  '99942': { a: 0.9224, e: 0.1912, i: 3.331, raan: 204.46, argp: 126.39, M: 222.45 },
  '433': { a: 1.458, e: 0.2227, i: 10.83, raan: 304.29, argp: 178.91, M: 310.0 },
  '101955': { a: 1.126, e: 0.2037, i: 6.03, raan: 2.06, argp: 66.22, M: 101.7 },
  '3200': { a: 1.271, e: 0.8899, i: 22.26, raan: 265.22, argp: 322.17, M: 35.8 },
  '162173': { a: 1.189, e: 0.190, i: 7.62, raan: 35.7, argp: 286.9, M: 81.2 },
  '65803': { a: 1.271, e: 0.335, i: 8.75, raan: 203.9, argp: 126.6, M: 250.4 },
}

export const demoNeos = [
  {
    id: '99942',
    name: '99942 Apophis',
    designation: '2004 MN4',
    is_potentially_hazardous: true,
    absolute_magnitude: 19.7,
    estimated_diameter_min_km: 0.31,
    estimated_diameter_max_km: 0.68,
    nasa_jpl_url: 'https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr=99942',
    risk_score: 72.4,
    risk_tier: 'HIGH',
    approach_date: '2029-04-13T00:00:00',
    miss_distance_km: 32000,
    miss_distance_ld: 0.083,
    relative_velocity_kmps: 7.42,
  },
  {
    id: '433',
    name: '433 Eros',
    designation: 'A898 PA',
    is_potentially_hazardous: false,
    absolute_magnitude: 11.2,
    estimated_diameter_min_km: 16.8,
    estimated_diameter_max_km: 37.6,
    nasa_jpl_url: 'https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr=433',
    risk_score: 58.1,
    risk_tier: 'HIGH',
    approach_date: '2026-01-24T00:00:00',
    miss_distance_km: 22600000,
    miss_distance_ld: 58.79,
    relative_velocity_kmps: 5.96,
  },
  {
    id: '101955',
    name: '101955 Bennu',
    designation: '1999 RQ36',
    is_potentially_hazardous: true,
    absolute_magnitude: 20.6,
    estimated_diameter_min_km: 0.44,
    estimated_diameter_max_km: 0.56,
    nasa_jpl_url: 'https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr=101955',
    risk_score: 46.7,
    risk_tier: 'MEDIUM',
    approach_date: '2037-09-23T00:00:00',
    miss_distance_km: 750000,
    miss_distance_ld: 1.95,
    relative_velocity_kmps: 12.23,
  },
  {
    id: '3200',
    name: '3200 Phaethon',
    designation: '1983 TB',
    is_potentially_hazardous: true,
    absolute_magnitude: 14.6,
    estimated_diameter_min_km: 4.6,
    estimated_diameter_max_km: 6.3,
    nasa_jpl_url: 'https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr=3200',
    risk_score: 43.9,
    risk_tier: 'MEDIUM',
    approach_date: '2026-12-10T00:00:00',
    miss_distance_km: 10200000,
    miss_distance_ld: 26.53,
    relative_velocity_kmps: 19.12,
  },
  {
    id: '162173',
    name: '162173 Ryugu',
    designation: '1999 JU3',
    is_potentially_hazardous: true,
    absolute_magnitude: 19.2,
    estimated_diameter_min_km: 0.82,
    estimated_diameter_max_km: 0.92,
    nasa_jpl_url: 'https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr=162173',
    risk_score: 36.5,
    risk_tier: 'MEDIUM',
    approach_date: '2027-06-05T00:00:00',
    miss_distance_km: 3650000,
    miss_distance_ld: 9.5,
    relative_velocity_kmps: 8.91,
  },
  {
    id: '65803',
    name: '65803 Didymos',
    designation: '1996 GT',
    is_potentially_hazardous: true,
    absolute_magnitude: 18.2,
    estimated_diameter_min_km: 0.72,
    estimated_diameter_max_km: 0.88,
    nasa_jpl_url: 'https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr=65803',
    risk_score: 31.2,
    risk_tier: 'MEDIUM',
    approach_date: '2028-11-12T00:00:00',
    miss_distance_km: 7200000,
    miss_distance_ld: 18.73,
    relative_velocity_kmps: 6.54,
  },
]

export function getDemoNEOs(params = {}) {
  const page = Number(params.page || 1)
  const limit = Number(params.limit || 30)
  const sortBy = params.sort_by || 'risk_score'
  const sortDir = params.sort_dir || 'desc'
  const hazardousOnly = params.hazardous_only === true || params.hazardous_only === 'true'

  const filtered = hazardousOnly
    ? demoNeos.filter(neo => neo.is_potentially_hazardous)
    : demoNeos

  const sorted = [...filtered].sort((a, b) => {
    const av = a[sortBy] ?? 0
    const bv = b[sortBy] ?? 0
    if (typeof av === 'string') {
      return sortDir === 'desc' ? bv.localeCompare(av) : av.localeCompare(bv)
    }
    return sortDir === 'desc' ? bv - av : av - bv
  })

  const start = (page - 1) * limit
  return {
    demo: true,
    total: sorted.length,
    page,
    limit,
    items: sorted.slice(start, start + limit),
  }
}

export function getDemoNEO(id) {
  return demoNeos.find(neo => neo.id === id) || demoNeos[0]
}

export function getDemoOrbit(id) {
  const neo = getDemoNEO(id)
  const el = DEMO_ELEMENTS[id] || DEMO_ELEMENTS['99942']
  const path = []
  const inclination = (el.i * Math.PI) / 180
  const raan = (el.raan * Math.PI) / 180
  const phase = (el.M * Math.PI) / 180

  for (let step = 0; step <= 300; step += 1) {
    const t = (step / 300) * 30
    const theta = phase + (step / 300) * Math.PI * 2
    const r = (el.a * (1 - el.e * el.e)) / (1 + el.e * Math.cos(theta))
    const xOrb = r * Math.cos(theta)
    const yOrb = r * Math.sin(theta)
    const x = xOrb * Math.cos(raan) - yOrb * Math.sin(raan) * Math.cos(inclination)
    const y = xOrb * Math.sin(raan) + yOrb * Math.cos(raan) * Math.cos(inclination)
    const z = yOrb * Math.sin(inclination)
    path.push({ t, x, y, z })
  }

  return {
    demo: true,
    neo_id: id,
    elements: el,
    path,
    closest_approach: {
      t: 12.4,
      km: neo.miss_distance_km,
      ld: neo.miss_distance_ld,
    },
  }
}

export function getDemoMonteCarlo(id) {
  const neo = getDemoNEO(id)
  const mean = neo.miss_distance_km
  const std = Math.max(12000, mean * 0.035)
  const histogram_km = Array.from({ length: 80 }, (_, i) => {
    const wave = Math.sin(i * 0.55) * 0.4 + Math.cos(i * 0.19) * 0.25
    return Math.max(1000, mean + wave * std)
  }).sort((a, b) => a - b)

  return {
    demo: true,
    neo_id: id,
    mean_miss_km: mean,
    std_miss_km: std,
    p05_miss_km: Math.max(1000, mean - std * 1.6),
    p95_miss_km: mean + std * 1.6,
    mean_miss_ld: neo.miss_distance_ld,
    corridor: [],
    histogram_km,
  }
}

export function getDemoHistory(id, limit = 24) {
  const neo = getDemoNEO(id)
  const year = 2026
  return Array.from({ length: Math.min(limit, 12) }, (_, i) => {
    const scale = 0.82 + Math.abs(Math.sin(i * 0.73)) * 0.85
    return {
      approach_date: `${year - 10 + i}-0${(i % 9) + 1}-15T00:00:00`,
      miss_distance_km: neo.miss_distance_km * scale,
      miss_distance_ld: neo.miss_distance_ld * scale,
      relative_velocity_kmps: neo.relative_velocity_kmps * (0.9 + (i % 4) * 0.04),
      uncertainty_plus_km: neo.miss_distance_km * 0.04,
      uncertainty_minus_km: neo.miss_distance_km * 0.03,
    }
  })
}
