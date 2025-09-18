import axios from 'axios'
import toast from 'react-hot-toast'

// Create axios instance
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Cache for GET requests
const cache = new Map()
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Handle caching for GET requests
    if (config.method === 'get' && !config.skipCache) {
      const cacheKey = `${config.url}?${new URLSearchParams(config.params).toString()}`
      const cached = cache.get(cacheKey)
      
      if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
        // Return cached data
        config.adapter = () => Promise.resolve({
          data: cached.data,
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
        })
      }
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    // Cache successful GET responses
    if (response.config.method === 'get' && !response.config.skipCache) {
      const cacheKey = `${response.config.url}?${new URLSearchParams(response.config.params).toString()}`
      cache.set(cacheKey, {
        data: response.data,
        timestamp: Date.now(),
      })
    }

    return response
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      
      // Handle authentication errors
      if (status === 401) {
        localStorage.removeItem('authToken')
        window.location.href = '/login'
        return Promise.reject(error)
      }
      
      // Handle other HTTP errors
      const message = data?.detail || data?.message || `HTTP Error ${status}`
      toast.error(message)
    } else if (error.request) {
      // Network error
      toast.error('Network error. Please check your connection.')
    } else {
      // Other errors
      toast.error('An unexpected error occurred.')
    }
    
    return Promise.reject(error)
  }
)

// Clear cache function
export const clearCache = () => {
  cache.clear()
}

// Auth API
export const auth = {
  login: (credentials) => api.post('/admin/login', credentials),
  
  getCurrentUser: () => api.get('/admin/me'),
}

// Athletes API
export const athletes = {
  getAll: (params = {}) => api.get('/athletes', { params }),
  
  getById: (id) => api.get(`/athletes/${id}`),
  
  getStats: (id) => api.get(`/athletes/${id}/stats`),
  
  getSubmissions: (id, params = {}) => api.get(`/athletes/${id}/submissions`, { params }),
  
  update: (id, data) => api.put(`/athletes/${id}`, data),
  
  verify: (id) => api.post(`/athletes/${id}/verify`),
  
  delete: (id) => api.delete(`/athletes/${id}`),
}

// Submissions API  
export const submissions = {
  getAll: (params = {}) => api.get('/submissions', { params }),
  
  getById: (id) => api.get(`/submissions/${id}`),
  
  verify: (id) => api.put(`/submissions/${id}/verify`),
  
  delete: (id) => api.delete(`/submissions/${id}`),
  
  getLeaderboard: (params = {}) => api.get('/submissions/leaderboard/overall', { params }),
  
  getAnalytics: () => api.get('/submissions/analytics/summary'),
}

// Admin API
export const admin = {
  getDashboard: () => api.get('/admin/dashboard'),
  
  getPendingReview: (params = {}) => api.get('/admin/submissions/pending-review', { params }),
  
  getFlagged: (params = {}) => api.get('/admin/submissions/flagged', { params }),
  
  approveSubmission: (id) => api.post(`/admin/submissions/${id}/approve`),
  
  rejectSubmission: (id, reason) => api.post(`/admin/submissions/${id}/reject`, { reason }),
  
  getRecentAthletes: (params = {}) => api.get('/admin/athletes/recent', { params }),
  
  getSystemHealth: () => api.get('/admin/system/health'),
  
  getExerciseMetrics: () => api.get('/admin/reports/exercise-metrics'),
  
  getAuditLog: (params = {}) => api.get('/admin/audit-log', { params }),
}

// Generic API functions
export const fetchWithRetry = async (fn, retries = 3, delay = 1000) => {
  try {
    return await fn()
  } catch (error) {
    if (retries > 0 && error.response?.status >= 500) {
      await new Promise(resolve => setTimeout(resolve, delay))
      return fetchWithRetry(fn, retries - 1, delay * 2)
    }
    throw error
  }
}

// Upload file with progress
export const uploadFile = (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)
  
  return api.post('/uploads', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress) {
        const progress = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        )
        onProgress(progress)
      }
    },
  })
}

// Health check
export const healthCheck = () => api.get('/health', { skipCache: true })

export default api