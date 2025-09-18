import React from 'react'
import { clsx } from 'clsx'

const LoadingSpinner = ({ 
  size = 'md', 
  fullScreen = false, 
  className = '',
  message = ''
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  }

  const spinner = (
    <div className={clsx('flex items-center justify-center', className)}>
      <div className="flex flex-col items-center space-y-3">
        <div
          className={clsx(
            'border-4 border-secondary-200 border-t-primary-600 rounded-full animate-spin',
            sizeClasses[size]
          )}
        />
        {message && (
          <p className="text-sm text-secondary-600 animate-pulse">
            {message}
          </p>
        )}
      </div>
    </div>
  )

  if (fullScreen) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-secondary-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-secondary-200 border-t-primary-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-secondary-600 animate-pulse">
            {message || 'Loading...'}
          </p>
        </div>
      </div>
    )
  }

  return spinner
}

export default LoadingSpinner