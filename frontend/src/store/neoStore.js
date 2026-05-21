import { create } from 'zustand'

export const useNeoStore = create((set, get) => ({
  // Data
  neos: [],
  total: 0,
  loading: false,
  error: null,
  demoMode: false,

  // Selection
  selectedNeo: null,
  activeTab: 'table',   // 'table' | 'risk'

  // Filters
  hazardousOnly: false,
  searchQuery: '',
  sortBy: 'risk_score',
  sortDir: 'desc',
  page: 1,

  // Detail / orbit
  orbitData: null,
  monteCarloData: null,
  historyData: [],
  detailLoading: false,

  // 3D scene time
  scrubDay: 0,
  isPlaying: false,

  // Alerts
  wsConnected: false,
  toasts: [],
  alertLog: [],

  // ── Actions ────────────────────────────────────────────────────────────────
  setNeos: (neos, total) => set({ neos, total }),
  setLoading: (v) => set({ loading: v }),
  setError: (e) => set({ error: e }),
  setDemoMode: (v) => set({ demoMode: v }),
  setSelectedNeo: (neo) => set({ selectedNeo: neo, orbitData: null, monteCarloData: null, historyData: [] }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setHazardousOnly: (v) => set({ hazardousOnly: v, page: 1 }),
  setSearchQuery: (q) => set({ searchQuery: q }),
  setSortBy: (col) => {
    const { sortBy, sortDir } = get()
    if (sortBy === col) {
      set({ sortDir: sortDir === 'desc' ? 'asc' : 'desc' })
    } else {
      set({ sortBy: col, sortDir: 'desc' })
    }
  },
  setPage: (p) => set({ page: p }),
  setOrbitData: (d) => set({ orbitData: d }),
  setMonteCarloData: (d) => set({ monteCarloData: d }),
  setHistoryData: (d) => set({ historyData: d }),
  setDetailLoading: (v) => set({ detailLoading: v }),
  setScrubDay: (d) => set(state => ({ scrubDay: typeof d === 'function' ? d(state.scrubDay) : d })),
  setIsPlaying: (v) => set({ isPlaying: v }),
  setWsConnected: (v) => set({ wsConnected: v }),
  addToast: (t) => set(s => ({ toasts: [...s.toasts, { ...t, id: Date.now() }] })),
  removeToast: (id) => set(s => ({ toasts: s.toasts.filter(t => t.id !== id) })),
  setAlertLog: (l) => set({ alertLog: l }),
}))
