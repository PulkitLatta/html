import React, { useState } from 'react'
import { clsx } from 'clsx'
import { 
  ChevronLeft, 
  ChevronRight, 
  ChevronsLeft, 
  ChevronsRight,
  Search,
  Filter,
  Download,
  Eye,
  Edit,
  Trash2
} from 'lucide-react'

const DataTable = ({
  data = [],
  columns = [],
  loading = false,
  pagination = null,
  searchable = false,
  filterable = false,
  exportable = false,
  selectable = false,
  onRowClick = null,
  onEdit = null,
  onDelete = null,
  onView = null,
  className = ''
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedRows, setSelectedRows] = useState(new Set())
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' })

  // Filter data based on search
  const filteredData = searchable 
    ? data.filter(row => 
        columns.some(col => {
          const value = col.accessor ? row[col.accessor] : ''
          return String(value).toLowerCase().includes(searchTerm.toLowerCase())
        })
      )
    : data

  // Sort data
  const sortedData = [...filteredData].sort((a, b) => {
    if (!sortConfig.key) return 0
    
    const aValue = a[sortConfig.key]
    const bValue = b[sortConfig.key]
    
    if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1
    if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1
    return 0
  })

  const handleSort = (key) => {
    setSortConfig({
      key,
      direction: sortConfig.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc'
    })
  }

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedRows(new Set(sortedData.map((_, index) => index)))
    } else {
      setSelectedRows(new Set())
    }
  }

  const handleRowSelect = (index, checked) => {
    const newSelected = new Set(selectedRows)
    if (checked) {
      newSelected.add(index)
    } else {
      newSelected.delete(index)
    }
    setSelectedRows(newSelected)
  }

  const renderCell = (row, column) => {
    if (column.render) {
      return column.render(row[column.accessor], row)
    }
    return row[column.accessor]
  }

  const renderActions = (row, index) => {
    return (
      <div className="flex items-center space-x-2">
        {onView && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onView(row)
            }}
            className="p-1 text-secondary-400 hover:text-secondary-600"
            title="View"
          >
            <Eye className="w-4 h-4" />
          </button>
        )}
        
        {onEdit && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onEdit(row)
            }}
            className="p-1 text-secondary-400 hover:text-blue-600"
            title="Edit"
          >
            <Edit className="w-4 h-4" />
          </button>
        )}
        
        {onDelete && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDelete(row)
            }}
            className="p-1 text-secondary-400 hover:text-red-600"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className={clsx('card', className)}>
        <div className="animate-pulse">
          <div className="h-4 bg-secondary-200 rounded w-1/4 mb-4" />
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-4 bg-secondary-200 rounded" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={clsx('card p-0', className)}>
      {/* Header */}
      {(searchable || filterable || exportable) && (
        <div className="p-6 border-b border-secondary-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {searchable && (
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-secondary-400" />
                  <input
                    type="text"
                    placeholder="Search..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 input w-64"
                  />
                </div>
              )}
              
              {filterable && (
                <button className="btn btn-secondary">
                  <Filter className="w-4 h-4 mr-2" />
                  Filter
                </button>
              )}
            </div>
            
            {exportable && (
              <button className="btn btn-secondary">
                <Download className="w-4 h-4 mr-2" />
                Export
              </button>
            )}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              {selectable && (
                <th className="w-12">
                  <input
                    type="checkbox"
                    checked={selectedRows.size === sortedData.length && sortedData.length > 0}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="rounded"
                  />
                </th>
              )}
              
              {columns.map((column, index) => (
                <th
                  key={index}
                  className={clsx(
                    column.sortable && 'cursor-pointer hover:bg-secondary-100'
                  )}
                  onClick={() => column.sortable && handleSort(column.accessor)}
                >
                  <div className="flex items-center space-x-1">
                    <span>{column.title}</span>
                    {column.sortable && sortConfig.key === column.accessor && (
                      <span className={clsx(
                        'text-xs',
                        sortConfig.direction === 'asc' ? 'text-blue-600' : 'text-blue-600'
                      )}>
                        {sortConfig.direction === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
              
              {(onView || onEdit || onDelete) && (
                <th>Actions</th>
              )}
            </tr>
          </thead>
          
          <tbody>
            {sortedData.length === 0 ? (
              <tr>
                <td 
                  colSpan={columns.length + (selectable ? 1 : 0) + (onView || onEdit || onDelete ? 1 : 0)}
                  className="text-center py-8 text-secondary-500"
                >
                  No data available
                </td>
              </tr>
            ) : (
              sortedData.map((row, index) => (
                <tr
                  key={index}
                  className={clsx(
                    'hover:bg-secondary-50',
                    onRowClick && 'cursor-pointer',
                    selectedRows.has(index) && 'bg-primary-50'
                  )}
                  onClick={() => onRowClick?.(row)}
                >
                  {selectable && (
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedRows.has(index)}
                        onChange={(e) => handleRowSelect(index, e.target.checked)}
                        onClick={(e) => e.stopPropagation()}
                        className="rounded"
                      />
                    </td>
                  )}
                  
                  {columns.map((column, colIndex) => (
                    <td key={colIndex}>
                      {renderCell(row, column)}
                    </td>
                  ))}
                  
                  {(onView || onEdit || onDelete) && (
                    <td>
                      {renderActions(row, index)}
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination && (
        <div className="px-6 py-4 border-t border-secondary-200">
          <div className="flex items-center justify-between">
            <p className="text-sm text-secondary-700">
              Showing {((pagination.page - 1) * pagination.size) + 1} to{' '}
              {Math.min(pagination.page * pagination.size, pagination.total)} of{' '}
              {pagination.total} results
            </p>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => pagination.onPageChange(1)}
                disabled={pagination.page === 1}
                className="p-2 text-secondary-400 hover:text-secondary-600 disabled:opacity-50"
              >
                <ChevronsLeft className="w-4 h-4" />
              </button>
              
              <button
                onClick={() => pagination.onPageChange(pagination.page - 1)}
                disabled={pagination.page === 1}
                className="p-2 text-secondary-400 hover:text-secondary-600 disabled:opacity-50"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              
              <span className="px-3 py-1 text-sm">
                Page {pagination.page} of {pagination.pages}
              </span>
              
              <button
                onClick={() => pagination.onPageChange(pagination.page + 1)}
                disabled={pagination.page === pagination.pages}
                className="p-2 text-secondary-400 hover:text-secondary-600 disabled:opacity-50"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
              
              <button
                onClick={() => pagination.onPageChange(pagination.pages)}
                disabled={pagination.page === pagination.pages}
                className="p-2 text-secondary-400 hover:text-secondary-600 disabled:opacity-50"
              >
                <ChevronsRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DataTable