import React from 'react'
import { clsx } from 'clsx'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

const KPICard = ({ 
  title, 
  value, 
  unit = '',
  change = null,
  changeType = 'neutral', // 'positive', 'negative', 'neutral'
  icon: Icon,
  className = '',
  loading = false,
  onClick
}) => {
  const formatValue = (val) => {
    if (typeof val === 'number') {
      if (val >= 1000000) {
        return `${(val / 1000000).toFixed(1)}M`
      } else if (val >= 1000) {
        return `${(val / 1000).toFixed(1)}K`
      }
      return val.toLocaleString()
    }
    return val
  }

  const getTrendIcon = () => {
    if (changeType === 'positive') return <TrendingUp className="w-4 h-4" />
    if (changeType === 'negative') return <TrendingDown className="w-4 h-4" />
    return <Minus className="w-4 h-4" />
  }

  const getTrendColor = () => {
    if (changeType === 'positive') return 'text-green-600'
    if (changeType === 'negative') return 'text-red-600'
    return 'text-secondary-500'
  }

  if (loading) {
    return (
      <div className={clsx('card animate-pulse', className)}>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="h-4 bg-secondary-200 rounded mb-2" />
            <div className="h-8 bg-secondary-200 rounded mb-2" />
            <div className="h-3 bg-secondary-200 rounded w-16" />
          </div>
          <div className="w-12 h-12 bg-secondary-200 rounded-lg" />
        </div>
      </div>
    )
  }

  return (
    <div 
      className={clsx(
        'card hover:shadow-md transition-shadow cursor-pointer',
        onClick && 'hover:border-primary-200',
        className
      )}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-secondary-600 mb-1">
            {title}
          </p>
          
          <div className="flex items-baseline space-x-1 mb-2">
            <span className="text-2xl font-bold text-secondary-900">
              {formatValue(value)}
            </span>
            {unit && (
              <span className="text-sm text-secondary-500">
                {unit}
              </span>
            )}
          </div>
          
          {change !== null && (
            <div className={clsx('flex items-center space-x-1 text-sm', getTrendColor())}>
              {getTrendIcon()}
              <span>
                {changeType === 'positive' && '+'}
                {change}%
              </span>
              <span className="text-secondary-500">vs last period</span>
            </div>
          )}
        </div>
        
        {Icon && (
          <div className="ml-4">
            <div className="w-12 h-12 bg-primary-50 rounded-lg flex items-center justify-center">
              <Icon className="w-6 h-6 text-primary-600" />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default KPICard