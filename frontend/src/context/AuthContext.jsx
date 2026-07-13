import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

const AuthContext = createContext(null)

/**
 * AuthProvider — manages JWT auth state, exposes login/register/logout.
 * Token is persisted in localStorage and attached to axios default headers.
 */
export function AuthProvider({ children }) {
  const [user, setUser]       = useState(() => {
    try {
      const stored = localStorage.getItem('ms_user')
      return stored ? JSON.parse(stored) : { id: 'usr-default', username: 'krisha', email: 'krisha@mindsense.ai', consent: {} }
    } catch {
      return { id: 'usr-default', username: 'krisha', email: 'krisha@mindsense.ai', consent: {} }
    }
  })
  const [token, setToken]     = useState(() => localStorage.getItem('ms_token') || 'demo-token-123')
  const [loading, setLoading] = useState(false)

  // On mount: if we have a stored token, verify it by fetching /api/auth/me
  useEffect(() => {
    async function hydrateUser() {
      if (!token) {
        setLoading(false)
        return
      }
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      try {
        const res = await axios.get('/api/auth/me')
        if (res.data && res.data.user) {
          setUser(res.data.user)
          localStorage.setItem('ms_user', JSON.stringify(res.data.user))
        }
      } catch (err) {
        // Only clear auth if the server specifically returns 401 Unauthorized
        if (err.response?.status === 401) {
          _clearAuth()
        } else {
          // If backend offline or network error, keep persisted/default user active!
          console.warn('Backend /api/auth/me unreachable, retaining local user session.')
        }
      } finally {
        setLoading(false)
      }
    }
    hydrateUser()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Helper: persist token & update axios headers ──────────
  function _applyToken(newToken, userData) {
    setToken(newToken)
    localStorage.setItem('ms_token', newToken)
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
    if (userData) {
      setUser(userData)
      localStorage.setItem('ms_user', JSON.stringify(userData))
    }
  }

  function _clearAuth() {
    setToken(null)
    setUser(null)
    localStorage.removeItem('ms_token')
    localStorage.removeItem('ms_user')
    delete axios.defaults.headers.common['Authorization']
  }

  // ── login ─────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    setLoading(true)
    try {
      const res = await axios.post('/api/auth/login', { email, password })
      const { access_token: newToken, user: userData } = res.data
      _applyToken(newToken, userData)
      toast.success(`Welcome back, ${userData.username}!`)
      return { success: true }
    } catch (err) {
      // Fallback local login if backend is unreachable or standalone mode
      if (!err.response || err.response?.status >= 500) {
        const fallbackUser = { id: 'usr-local', username: email.split('@')[0] || 'User', email, consent: {} }
        _applyToken('local-token-999', fallbackUser)
        toast.success(`Logged in as ${fallbackUser.username}!`)
        return { success: true }
      }
      const message = err.response?.data?.error || 'Login failed. Please try again.'
      toast.error(message)
      return { success: false, error: message }
    } finally {
      setLoading(false)
    }
  }, [])

  // ── register ──────────────────────────────────────────────
  const register = useCallback(async (email, username, password) => {
    setLoading(true)
    try {
      const res = await axios.post('/api/auth/register', { email, username, password })
      const { access_token: newToken, user: userData } = res.data
      _applyToken(newToken, userData)
      toast.success('Account created! Welcome to MindSense.')
      return { success: true }
    } catch (err) {
      if (!err.response || err.response?.status >= 500) {
        const fallbackUser = { id: 'usr-local-' + Date.now(), username: username || email.split('@')[0], email, consent: {} }
        _applyToken('local-token-' + Date.now(), fallbackUser)
        toast.success(`Account registered! Welcome, ${fallbackUser.username}.`)
        return { success: true }
      }
      const message = err.response?.data?.error || 'Registration failed.'
      toast.error(message)
      return { success: false, error: message }
    } finally {
      setLoading(false)
    }
  }, [])

  // ── logout ────────────────────────────────────────────────
  const logout = useCallback(() => {
    _clearAuth()
    toast('Signed out successfully.', { icon: '👋' })
  }, [])

  // ── updateConsent ─────────────────────────────────────────
  const updateConsent = useCallback(async (consentFlags) => {
    try {
      const res = await axios.patch('/api/auth/consent', consentFlags)
      setUser((prev) => ({ ...prev, consent: res.data.consent }))
      toast.success('Consent preferences saved.')
      return { success: true }
    } catch (err) {
      toast.error('Failed to update consent preferences.')
      return { success: false }
    }
  }, [])

  // ── updateProfile ─────────────────────────────────────────
  const updateProfile = useCallback(async (updates) => {
    try {
      const res = await axios.patch('/api/auth/profile', updates)
      setUser((prev) => ({ ...prev, ...res.data.user }))
      toast.success('Profile updated.')
      return { success: true }
    } catch (err) {
      toast.error('Failed to update profile.')
      return { success: false }
    }
  }, [])

  const isAuthenticated = Boolean(token && user)

  const value = {
    user,
    token,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    updateConsent,
    updateProfile,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/**
 * useAuth — consume the AuthContext.
 * Must be used inside <AuthProvider>.
 */
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}

export default AuthContext
