import axios from 'axios'
import toast from 'react-hot-toast'

// Base URL for the API
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Auth token management
const getAuthToken = () => {
  return localStorage.getItem('auth_token')
}

const setAuthToken = (token) => {
  localStorage.setItem('auth_token', token)
}

const removeAuthToken = () => {
  localStorage.removeItem('auth_token')
}

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = getAuthToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling and token refresh
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post(`${BASE_URL}/api/auth/refresh`, {
            refresh_token: refreshToken
          })
          
          const { access_token } = response.data
          setAuthToken(access_token)
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          
          return api(originalRequest)
        } catch (refreshError) {
          // Refresh failed, redirect to login
          removeAuthToken()
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      } else {
        // No refresh token, redirect to login
        removeAuthToken()
        window.location.href = '/login'
      }
    }

    // Handle other errors
    if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.')
    } else if (error.response?.status === 403) {
      toast.error('Access denied. You do not have permission.')
    } else if (error.response?.status === 429) {
      toast.error('Too many requests. Please slow down.')
    }

    return Promise.reject(error)
  }
)

// Simple in-memory cache for GET requests
const cache = new Map()
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

const getCacheKey = (method, url, params) => {
  return `${method}:${url}:${JSON.stringify(params || {})}`
}

// Cached GET request
const cachedGet = async (url, config = {}) => {
  const cacheKey = getCacheKey('GET', url, config.params)
  const cached = cache.get(cacheKey)
  
  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return { data: cached.data, fromCache: true }
  }
  
  const response = await api.get(url, config)
  
  // Cache successful responses
  if (response.status === 200) {
    cache.set(cacheKey, {
      data: response.data,
      timestamp: Date.now()
    })
  }
  
  return response
}

// API methods
export const authAPI = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  refresh: (refreshToken) => api.post('/api/auth/refresh', { refresh_token: refreshToken }),
  logout: () => api.post('/api/auth/logout'),
}

export const usersAPI = {
  getProfile: () => cachedGet('/api/athletes/me'),
  updateProfile: (data) => api.put('/api/athletes/me', data),
  getUser: (id) => cachedGet(`/api/athletes/${id}`),
  searchAthletes: (query, params = {}) => cachedGet('/api/athletes/search', { params: { q: query, ...params } }),
}

export const submissionsAPI = {
  getMySubmissions: (params = {}) => cachedGet('/api/submissions/me', { params }),
  getSubmission: (id) => cachedGet(`/api/submissions/${id}`),
  createSubmission: (data) => api.post('/api/submissions', data),
  updateSubmission: (id, data) => api.put(`/api/submissions/${id}`, data),
  deleteSubmission: (id) => api.delete(`/api/submissions/${id}`),
  getAnalysis: (id) => cachedGet(`/api/submissions/${id}/analysis`),
}

export const leaderboardAPI = {
  getLeaderboard: (params = {}) => cachedGet('/api/leaderboard', { params }),
}

export const adminAPI = {
  getUsers: (params = {}) => cachedGet('/api/admin/users', { params }),
  getUser: (id) => cachedGet(`/api/admin/users/${id}`),
  updateUser: (id, data) => api.put(`/api/admin/users/${id}`, data),
  deleteUser: (id) => api.delete(`/api/admin/users/${id}`),
  
  getSubmissions: (params = {}) => cachedGet('/api/admin/submissions', { params }),
  getSubmissionStats: (params = {}) => cachedGet('/api/admin/submissions/stats', { params }),
  
  getAnalytics: (params = {}) => cachedGet('/api/admin/analytics/usage', { params }),
  getUserActivity: (id, params = {}) => cachedGet(`/api/admin/users/${id}/activity`, { params }),
  
  getSystemSettings: () => cachedGet('/api/admin/system/settings'),
  updateSystemSetting: (key, data) => api.post('/api/admin/system/settings', { key, ...data }),
  
  bulkUpdateSubmissions: (data) => api.post('/api/admin/bulk/submissions/update', data),
  bulkUpdateUsers: (data) => api.post('/api/admin/bulk/users/update', data),
}

export const healthAPI = {
  check: () => api.get('/api/health'),
}

// Utility functions
export const clearCache = () => {
  cache.clear()
}

export const invalidateCache = (pattern) => {
  const keysToDelete = []
  for (const key of cache.keys()) {
    if (key.includes(pattern)) {
      keysToDelete.push(key)
    }
  }
  keysToDelete.forEach(key => cache.delete(key))
}

// Export configured axios instance and auth helpers
export { api, getAuthToken, setAuthToken, removeAuthToken }
export default api