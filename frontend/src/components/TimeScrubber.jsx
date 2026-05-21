import { useRef, useEffect } from 'react'
import { useNeoStore } from '../store/neoStore'

export function TimeScrubber() {
  const { scrubDay, setScrubDay, isPlaying, setIsPlaying } = useNeoStore()
  const rafRef = useRef(null)
  const lastRef = useRef(null)

  useEffect(() => {
    if (isPlaying) {
      const tick = (ts) => {
        if (lastRef.current != null) {
          const dt = (ts - lastRef.current) / 1000  // seconds
          setScrubDay(prev => {
            const next = prev + dt * 2  // 2 days/sec playback
            return next >= 30 ? 0 : next
          })
        }
        lastRef.current = ts
        rafRef.current = requestAnimationFrame(tick)
      }
      rafRef.current = requestAnimationFrame(tick)
    } else {
      cancelAnimationFrame(rafRef.current)
      lastRef.current = null
    }
    return () => cancelAnimationFrame(rafRef.current)
  }, [isPlaying])

  return (
    <div className="time-scrubber">
      <button
        id="scrubber-rewind"
        className="scrubber-btn"
        onClick={() => setScrubDay(0)}
        title="Rewind to T+0"
      >⏮</button>

      <button
        id="scrubber-play-pause"
        className={`scrubber-btn ${isPlaying ? 'active' : ''}`}
        onClick={() => setIsPlaying(!isPlaying)}
        title={isPlaying ? 'Pause' : 'Play'}
      >{isPlaying ? '⏸' : '▶'}</button>

      <input
        id="scrubber-range"
        type="range"
        className="scrubber-track"
        min={0}
        max={30}
        step={0.1}
        value={scrubDay}
        onChange={e => {
          setIsPlaying(false)
          setScrubDay(parseFloat(e.target.value))
        }}
      />

      <span className="scrubber-day">T+{scrubDay.toFixed(1)}d</span>
    </div>
  )
}
