import React from 'react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import clsx from 'clsx'

const KPICard = ({ 
  title, 
  value, 
  change, 
  changeType = 'percentage', 
  trend,
  icon: Icon,
  color = 'blue',
  isLoading = false,
  className = ''
}) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    green: 'bg-green-50 text-green-600 border-green-200', 
    yellow: 'bg-yellow-50 text-yellow-600 border-yellow-200',
    red: 'bg-red-50 text-red-600 border-red-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200',
    indigo: 'bg-indigo-50 text-indigo-600 border-indigo-200',
  }

  const getTrendIcon = () => {
    if (trend === 'up') return TrendingUp
    if (trend === 'down') return TrendingDown
    return Minus
  }

  const getTrendColor = () => {
    if (trend === 'up') return 'text-green-600'
    if (trend === 'down') return 'text-red-600'
    return 'text-gray-500'
  }

  const formatChange = (value, type) => {
    if (value === undefined || value === null) return ''
    
    const prefix = value > 0 ? '+' : ''
    const suffix = type === 'percentage' ? '%' : ''
    
    return `${prefix}${value}${suffix}`
  }

  const TrendIcon = getTrendIcon()

  if (isLoading) {
    return (
      <div className={clsx('card p-6 animate-pulse', className)}>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-16 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-20"></div>
          </div>
          <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
        </div>
      </div>
    )
  }

  return (
    <div className={clsx('card p-6 card-hover', className)}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <h3 className="text-sm font-medium text-gray-500 mb-1">
            {title}
          </h3>
          
          <div className="text-2xl font-bold text-gray-900 mb-2">
            {value}
          </div>
          
          {change !== undefined && (
            <div className="flex items-center text-sm">
              <TrendIcon className={clsx('w-4 h-4 mr-1', getTrendColor())} />
              <span className={getTrendColor()}>
                {formatChange(change, changeType)}
              </span>
              <span className="text-gray-500 ml-1">from last period</span>
            </div>
          )}
        </div>
        
        {Icon && (
          <div className={clsx(
            'p-3 rounded-lg border',
            colorClasses[color] || colorClasses.blue
          )}>
            <Icon className="w-6 h-6" />
          </div>
        )}
      </div>
    </div>
  )
}

export default KPICard