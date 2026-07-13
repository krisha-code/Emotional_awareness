import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
} from 'react'
import toast from 'react-hot-toast'
import { fusionAPI, historyAPI } from '../api/client.js'

const EmotionContext = createContext(null)

/**
 * EmotionProvider — manages analysis sessions, history, and trends.
 */
export function EmotionProvider({ children }) {
  const [currentSession, setCurrentSession] = useState(null)
  const [sessions, setSessions]             = useState([])
  const [trends, setTrends]                 = useState(null)
  const [isAnalyzing, setIsAnalyzing]       = useState(false)
  const [lastResult, setLastResult]         = useState(null)
  const [historyPage, setHistoryPage]       = useState(1)
  const [historyTotal, setHistoryTotal]     = useState(0)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [trendsLoading, setTrendsLoading]   = useState(false)

  // AbortController ref for cancellable requests
  const analyzeAbortRef = useRef(null)

  /**
   * analyzeAll — sends face + text + audio to /api/fusion/analyze.
   * @param {string|null}  imageBase64 — base64 JPEG from FaceCapture
   * @param {string|null}  text        — text from TextInput
   * @param {Blob|null}    audioBlob   — audio blob from AudioRecorder
   * @param {object|null}  wearable    — optional HR/HRV/EDA values
   */
  const analyzeAll = useCallback(async (imageBase64, text, audioBlob, wearable = null) => {
    // Cancel any in-flight request
    if (analyzeAbortRef.current) {
      analyzeAbortRef.current.abort()
    }
    analyzeAbortRef.current = new AbortController()

    setIsAnalyzing(true)
    try {
      const formData = new FormData()
      if (imageBase64) formData.append('image_base64', imageBase64)
      if (text)        formData.append('text', text)
      if (audioBlob)   formData.append('audio', audioBlob, 'recording.webm')
      if (wearable)    formData.append('wearable', JSON.stringify(wearable))

      const result = await fusionAPI.analyze(formData, analyzeAbortRef.current.signal)

      setLastResult(result)
      setCurrentSession({
        id:        result.session_id,
        timestamp: new Date().toISOString(),
        result,
      })

      // Prepend to sessions list so it appears at the top of history
      setSessions((prev) => [{ id: result.session_id, timestamp: new Date().toISOString(), result }, ...prev])

      // Auto-announce severity for screen readers
      if (result.severity === 'critical') {
        toast.error('⚠ Critical distress detected. Crisis resources are available below.', {
          duration: 8000,
        })
      } else if (result.severity === 'high') {
        toast('High distress level detected. Consider speaking to someone.', {
          icon: '⚠️',
          duration: 5000,
        })
      } else {
        toast.success('Analysis complete.')
      }

      return result
    } catch (err) {
      if (err.name === 'AbortError' || err.name === 'CanceledError') return null
      const message = err.response?.data?.error || 'Analysis failed. Please try again.'
      toast.error(message)
      return null
    } finally {
      setIsAnalyzing(false)
    }
  }, [])

  /**
   * loadHistory — fetches paginated session history.
   * @param {number} page  — page number (1-indexed)
   * @param {object} filters — { emotion, severity, start_date, end_date }
   */
  const loadHistory = useCallback(async (page = 1, filters = {}) => {
    setHistoryLoading(true)
    try {
      const data = await historyAPI.getSessions({ page, per_page: 10, ...filters })
      setSessions(data.sessions || [])
      setHistoryTotal(data.total || 0)
      setHistoryPage(page)
    } catch (err) {
      toast.error('Failed to load session history.')
    } finally {
      setHistoryLoading(false)
    }
  }, [])

  /**
   * loadTrends — fetches longitudinal emotion trends.
   * @param {number} days — look-back window (7, 30, or 0 for all)
   */
  const loadTrends = useCallback(async (days = 7) => {
    setTrendsLoading(true)
    try {
      const data = await historyAPI.getTrends({ days })
      setTrends(data)
    } catch (err) {
      toast.error('Failed to load trend data.')
    } finally {
      setTrendsLoading(false)
    }
  }, [])

  /**
   * loadSessionDetail — fetches a single session by ID.
   */
  const loadSessionDetail = useCallback(async (sessionId) => {
    try {
      const data = await historyAPI.getSession(sessionId)
      return data
    } catch (err) {
      toast.error('Failed to load session details.')
      return null
    }
  }, [])

  /**
   * clearSession — resets the current working session.
   */
  const clearSession = useCallback(() => {
    setCurrentSession(null)
    setLastResult(null)
  }, [])

  const value = {
    currentSession,
    sessions,
    trends,
    isAnalyzing,
    lastResult,
    historyPage,
    historyTotal,
    historyLoading,
    trendsLoading,
    analyzeAll,
    loadHistory,
    loadTrends,
    loadSessionDetail,
    clearSession,
  }

  return (
    <EmotionContext.Provider value={value}>
      {children}
    </EmotionContext.Provider>
  )
}

/**
 * useEmotion — consume the EmotionContext.
 */
export function useEmotion() {
  const ctx = useContext(EmotionContext)
  if (!ctx) {
    throw new Error('useEmotion must be used within an EmotionProvider')
  }
  return ctx
}

export default EmotionContext
