import React, { useState } from 'react'
import { ChevronUp, ChevronDown, Search, MoreHorizontal } from 'lucide-react'
import clsx from 'clsx'

const DataTable = ({
  data = [],
  columns = [],
  isLoading = false,
  searchable = true,
  sortable = true,
  pagination = true,
  pageSize = 10,
  onRowClick = null,
  className = ''
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [sortColumn, setSortColumn] = useState(null)
  const [sortDirection, setSortDirection] = useState('asc')
  const [currentPage, setCurrentPage] = useState(1)

  // Filter data based on search term
  const filteredData = data.filter(row =>
    !searchTerm || 
    Object.values(row).some(value =>
      value && value.toString().toLowerCase().includes(searchTerm.toLowerCase())
    )
  )

  // Sort data
  const sortedData = [...filteredData].sort((a, b) => {
    if (!sortColumn) return 0

    let aValue = a[sortColumn]
    let bValue = b[sortColumn]

    // Handle null/undefined values
    if (aValue == null) aValue = ''
    if (bValue == null) bValue = ''

    // Convert to strings for comparison if not numbers
    if (typeof aValue !== 'number' || typeof bValue !== 'number') {
      aValue = aValue.toString().toLowerCase()
      bValue = bValue.toString().toLowerCase()
    }

    if (sortDirection === 'asc') {
      return aValue > bValue ? 1 : aValue < bValue ? -1 : 0
    } else {
      return aValue < bValue ? 1 : aValue > bValue ? -1 : 0
    }
  })

  // Paginate data
  const totalPages = Math.ceil(sortedData.length / pageSize)
  const paginatedData = pagination
    ? sortedData.slice((currentPage - 1) * pageSize, currentPage * pageSize)
    : sortedData

  const handleSort = (column) => {
    if (!sortable || !column.sortable) return

    if (sortColumn === column.key) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column.key)
      setSortDirection('asc')
    }
  }

  const renderCell = (row, column) => {
    const value = row[column.key]

    if (column.render) {
      return column.render(value, row)
    }

    if (value == null) {
      return <span className="text-gray-400">—</span>
    }

    return value
  }

  const LoadingRow = () => (
    <tr className="animate-pulse">
      {columns.map((column, index) => (
        <td key={index} className="px-6 py-4">
          <div className="h-4 bg-gray-200 rounded"></div>
        </td>
      ))}
    </tr>
  )

  return (
    <div className={clsx('card overflow-hidden', className)}>
      {/* Search Bar */}
      {searchable && (
        <div className="p-4 border-b border-gray-200">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 input"
            />
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="table">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={clsx(
                    'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
                    sortable && column.sortable && 'cursor-pointer select-none hover:text-gray-700'
                  )}
                  onClick={() => handleSort(column)}
                >
                  <div className="flex items-center gap-1">
                    {column.title}
                    {sortable && column.sortable && (
                      <span className="flex flex-col">
                        <ChevronUp
                          className={clsx(
                            'w-3 h-3',
                            sortColumn === column.key && sortDirection === 'asc'
                              ? 'text-gray-900'
                              : 'text-gray-400'
                          )}
                        />
                        <ChevronDown
                          className={clsx(
                            'w-3 h-3 -mt-1',
                            sortColumn === column.key && sortDirection === 'desc'
                              ? 'text-gray-900'
                              : 'text-gray-400'
                          )}
                        />
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {isLoading ? (
              // Loading rows
              Array.from({ length: pageSize }).map((_, index) => (
                <LoadingRow key={index} />
              ))
            ) : paginatedData.length === 0 ? (
              // Empty state
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-6 py-12 text-center text-gray-500"
                >
                  {searchTerm ? 'No results found' : 'No data available'}
                </td>
              </tr>
            ) : (
              // Data rows
              paginatedData.map((row, rowIndex) => (
                <tr
                  key={row.id || rowIndex}
                  className={clsx(
                    'table-row',
                    onRowClick && 'cursor-pointer'
                  )}
                  onClick={() => onRowClick && onRowClick(row)}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                    >
                      {renderCell(row, column)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination && totalPages > 1 && (
        <div className="px-6 py-3 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, sortedData.length)} of {sortedData.length} results
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              Previous
            </button>
            
            {/* Page numbers */}
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const page = i + 1
              return (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={clsx(
                    'px-3 py-1 text-sm border rounded',
                    currentPage === page
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'border-gray-300 hover:bg-gray-100'
                  )}
                >
                  {page}
                </button>
              )
            })}
            
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default DataTable