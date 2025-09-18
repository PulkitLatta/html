import React, { useState, useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Loader } from 'lucide-react'
import { getAuthToken, usersAPI } from '@/api'

const ProtectedRoute = ({ children }) => {
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const location = useLocation()

  useEffect(() => {
    checkAuthentication()
  }, [])

  const checkAuthentication = async () => {
    const token = getAuthToken()
    
    if (!token) {
      setIsLoading(false)
      setIsAuthenticated(false)
      return
    }

    try {
      // Verify token by fetching user profile
      const response = await usersAPI.getProfile()
      setUser(response.data)
      setIsAuthenticated(true)
    } catch (error) {
      console.error('Authentication check failed:', error)
      setIsAuthenticated(false)
      // Token might be expired or invalid
      localStorage.removeItem('auth_token')
      localStorage.removeItem('refresh_token')
    } finally {
      setIsLoading(false)
    }
  }

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader className="w-8 h-8 animate-spin text-primary-600 mx-auto" />
          <p className="mt-4 text-gray-600">Verifying authentication...</p>
        </div>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Check if user has required permissions
  const requiredRole = getRequiredRole(location.pathname)
  if (requiredRole && !hasRequiredRole(user, requiredRole)) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full mx-4">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-6 bg-yellow-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Access Restricted
            </h2>
            
            <p className="text-gray-600 mb-6">
              You don't have permission to access this page. Please contact your administrator if you believe this is an error.
            </p>
            
            <button
              onClick={() => window.history.back()}
              className="btn-secondary w-full"
            >
              Go Back
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Render protected content with user context
  return React.cloneElement(children, { user })
}

// Helper function to determine required role for a route
const getRequiredRole = (pathname) => {
  if (pathname.startsWith('/admin')) {
    return 'admin'
  }
  // Add other role-based routes as needed
  return null
}

// Helper function to check if user has required role
const hasRequiredRole = (user, requiredRole) => {
  if (!user || !requiredRole) return true
  
  const userRole = user.role || 'athlete'
  
  // Role hierarchy: admin > coach > athlete
  const roleHierarchy = ['athlete', 'coach', 'admin']
  const userRoleIndex = roleHierarchy.indexOf(userRole)
  const requiredRoleIndex = roleHierarchy.indexOf(requiredRole)
  
  return userRoleIndex >= requiredRoleIndex
}

export default ProtectedRoute