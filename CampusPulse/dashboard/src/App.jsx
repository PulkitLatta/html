import React, { Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ProtectedRoute } from './components/ProtectedRoute'
import { useAuthStore } from './utils/authStore'
import LoadingSpinner from './components/LoadingSpinner'

// Lazy load pages for better performance
const Login = React.lazy(() => import('./pages/Login'))
const AdminDashboard = React.lazy(() => import('./pages/AdminDashboard'))
const AthleteProfile = React.lazy(() => import('./pages/AthleteProfile'))
const Leaderboard = React.lazy(() => import('./pages/Leaderboard'))

function App() {
  const { isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return <LoadingSpinner fullScreen />
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-secondary-50">
        <Suspense fallback={<LoadingSpinner fullScreen />}>
          <Routes>
            {/* Public routes */}
            <Route 
              path="/login" 
              element={
                isAuthenticated ? (
                  <Navigate to="/dashboard" replace />
                ) : (
                  <Login />
                )
              } 
            />
            
            {/* Protected routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/athlete/:id"
              element={
                <ProtectedRoute>
                  <AthleteProfile />
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/leaderboard"
              element={
                <ProtectedRoute>
                  <Leaderboard />
                </ProtectedRoute>
              }
            />
            
            {/* Default redirect */}
            <Route 
              path="/" 
              element={
                <Navigate 
                  to={isAuthenticated ? "/dashboard" : "/login"} 
                  replace 
                />
              } 
            />
            
            {/* Catch all - 404 */}
            <Route 
              path="*" 
              element={
                <div className="min-h-screen flex items-center justify-center bg-secondary-50">
                  <div className="text-center">
                    <h1 className="text-9xl font-bold text-secondary-200">404</h1>
                    <p className="text-2xl font-semibold text-secondary-600 mb-4">Page not found</p>
                    <p className="text-secondary-500 mb-8">The page you're looking for doesn't exist.</p>
                    <button
                      onClick={() => window.history.back()}
                      className="btn btn-primary"
                    >
                      Go Back
                    </button>
                  </div>
                </div>
              } 
            />
          </Routes>
        </Suspense>
      </div>
    </ErrorBoundary>
  )
}

export default App