import React, { Suspense } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AnimatePresence } from 'framer-motion'

import { AuthProvider, useAuth } from './context/AuthContext.jsx'
import { EmotionProvider } from './context/EmotionContext.jsx'
import Layout from './components/Layout/Layout.jsx'

// Pages
import Home        from './pages/Home.jsx'
import Analyze     from './pages/Analyze.jsx'
import ResultsPage from './pages/ResultsPage.jsx'
import History     from './pages/History.jsx'
import Journal     from './pages/Journal.jsx'
import Settings    from './pages/Settings.jsx'
import Login       from './pages/Login.jsx'
import Register    from './pages/Register.jsx'

// Loading fallback
function PageLoader() {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: '#0a0a0f',
      }}
    >
      <div className="loading-spinner-lg" aria-label="Loading page…" role="status" />
    </div>
  )
}

// Guard: redirect to /login if not authenticated
function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) return <PageLoader />
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  return children
}

// Guard: redirect authenticated users away from auth pages
function PublicRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()

  if (loading) return <PageLoader />
  if (isAuthenticated) return <Navigate to="/" replace />
  return children
}

// Animated page wrapper — wraps every page with framer-motion
function AnimatedRoutes() {
  const location = useLocation()

  return (
    <AnimatePresence mode="wait" initial={false}>
      <Routes location={location} key={location.pathname}>
        {/* Public routes */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          }
        />

        {/* Protected routes — wrapped in Layout */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout>
                <Home />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/analyze"
          element={
            <ProtectedRoute>
              <Layout>
                <Analyze />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/results"
          element={
            <ProtectedRoute>
              <Layout>
                <ResultsPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <Layout>
                <History />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/journal"
          element={
            <ProtectedRoute>
              <Layout>
                <Journal />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Layout>
                <Settings />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <EmotionProvider>
        {/* Skip to main content — accessibility */}
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>

        {/* Global toast notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#1a1a2e',
              color: '#F0F0FF',
              border: '1px solid rgba(255,255,255,0.10)',
              borderRadius: '12px',
              fontSize: '14px',
              backdropFilter: 'blur(12px)',
            },
            success: {
              iconTheme: { primary: '#43E97B', secondary: '#0a0a0f' },
            },
            error: {
              iconTheme: { primary: '#FF4757', secondary: '#fff' },
            },
          }}
        />

        <Suspense fallback={<PageLoader />}>
          <AnimatedRoutes />
        </Suspense>
      </EmotionProvider>
    </AuthProvider>
  )
}
