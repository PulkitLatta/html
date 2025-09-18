import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { auth } from './api'

const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Initialize authentication state
      initialize: async () => {
        const token = localStorage.getItem('authToken')
        if (!token) {
          set({ isLoading: false })
          return
        }

        set({ isLoading: true, error: null })
        
        try {
          const response = await auth.getCurrentUser()
          set({
            user: response.data,
            token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error) {
          // Token is invalid, clear it
          localStorage.removeItem('authToken')
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          })
        }
      },

      // Login
      login: async (credentials) => {
        set({ isLoading: true, error: null })
        
        try {
          const response = await auth.login(credentials)
          const { access_token, ...userData } = response.data
          
          // Store token
          localStorage.setItem('authToken', access_token)
          
          set({
            user: userData,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
          
          return { success: true }
        } catch (error) {
          const errorMessage = error.response?.data?.detail || 'Login failed'
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
            error: errorMessage,
          })
          
          return { success: false, error: errorMessage }
        }
      },

      // Logout
      logout: () => {
        localStorage.removeItem('authToken')
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        })
      },

      // Clear error
      clearError: () => set({ error: null }),

      // Update user data
      updateUser: (userData) => {
        set((state) => ({
          user: { ...state.user, ...userData }
        }))
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({ 
        user: state.user,
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
)

// Initialize auth state on app start
const initializeAuth = () => {
  useAuthStore.getState().initialize()
}

export { useAuthStore, initializeAuth }