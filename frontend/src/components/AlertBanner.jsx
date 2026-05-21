import { useEffect, useRef, useCallback } from 'react'
import { useNeoStore } from '../store/neoStore'
import { createAlertSocket } from '../api/neoApi'

export function AlertBanner() {
  const { toasts, removeToast, setWsConnected, addToast, demoMode } = useNeoStore()
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)
  const demoModeRef = useRef(demoMode)

  useEffect(() => {
    demoModeRef.current = demoMode
  }, [demoMode])

  const connect = useCallback(() => {
    wsRef.current = createAlertSocket(
      (msg) => {
        if (msg.type === 'alert') {
          addToast(msg)
          // Auto-dismiss after 8s
          setTimeout(() => removeToast(msg.id), 8000)
        }
      },
      () => setWsConnected(true),
      () => {
        setWsConnected(false)
        if (!demoModeRef.current) {
          // Reconnect after 5s
          reconnectTimer.current = setTimeout(connect, 5000)
        }
      }
    )
  }, [addToast, removeToast, setWsConnected])

  useEffect(() => {
    if (demoMode) {
      wsRef.current?.close()
      clearTimeout(reconnectTimer.current)
      setWsConnected(false)
      return
    }

    connect()
    return () => {
      wsRef.current?.close()
      clearTimeout(reconnectTimer.current)
    }
  }, [connect, demoMode, setWsConnected])

  return (
    <div className="alert-container">
      {toasts.map(toast => (
        <div key={toast.id} className="alert-toast">
          <div className="alert-toast-title">
            ⚠️ CLOSE APPROACH ALERT
          </div>
          <div className="alert-toast-body">
            <strong>{toast.neo_name}</strong> crossing at{' '}
            <span style={{ color: 'var(--risk-critical)' }}>
              {toast.miss_distance_ld?.toFixed(3)} LD
            </span>
            {' '}on {toast.approach_date}
          </div>
          <button
            id={`dismiss-alert-${toast.id}`}
            className="alert-dismiss"
            onClick={() => removeToast(toast.id)}
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  )
}
