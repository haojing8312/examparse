import React, { useMemo, useState } from 'react'
import { twMerge } from 'tailwind-merge'

export type Column<T> = {
  key: keyof T
  title: string
  render?: (value: any, row: T) => React.ReactNode
}

export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  searchKeys,
  initialPageSize = 20,
  className,
}: {
  columns: Column<T>[]
  data: T[]
  searchKeys?: Array<keyof T>
  initialPageSize?: number
  className?: string
}) {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(initialPageSize)
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    if (!query.trim()) return data
    const q = query.toLowerCase()
    const keys = searchKeys && searchKeys.length > 0 ? searchKeys : (columns.map((c) => c.key) as Array<keyof T>)
    return data.filter((row) =>
      keys.some((k) => String(row[k] ?? '').toLowerCase().includes(q))
    )
  }, [data, query, searchKeys, columns])

  const total = filtered.length
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const currentPage = Math.min(page, totalPages)
  const start = (currentPage - 1) * pageSize
  const pageRows = filtered.slice(start, start + pageSize)

  return (
    <div className={twMerge('space-y-2', className)}>
      <div className="flex items-center justify-between gap-2">
        <input
          className="h-9 w-60 rounded-md border border-border bg-transparent px-3 text-sm outline-none focus:ring-2 focus:ring-primary/60"
          placeholder="搜索..."
          value={query}
          onChange={(e) => { setPage(1); setQuery(e.target.value) }}
        />
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>每页</span>
          <select
            className="h-9 rounded-md border border-border bg-transparent px-2 outline-none"
            value={pageSize}
            onChange={(e) => { setPage(1); setPageSize(parseInt(e.target.value, 10)) }}
          >
            {[10, 20, 50, 100].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
          <span className="ml-2">共 {total} 条</span>
        </div>
      </div>

      <div className="overflow-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead className="bg-white/5">
            <tr>
              {columns.map((c) => (
                <th key={String(c.key)} className="px-3 py-2 text-left font-medium text-muted-foreground">{c.title}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr key={i} className="border-t border-border/60">
                {columns.map((c) => {
                  const value = row[c.key]
                  return (
                    <td key={String(c.key)} className="px-3 py-2">
                      {c.render ? c.render(value, row) : String(value ?? '')}
                    </td>
                  )
                })}
              </tr>
            ))}
            {pageRows.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="px-3 py-6 text-center text-muted-foreground">暂无数据</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-end gap-2 text-sm">
        <button
          className="btn btn-ghost h-8 px-3"
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={currentPage <= 1}
        >上一页</button>
        <span className="text-muted-foreground">{currentPage} / {totalPages}</span>
        <button
          className="btn btn-ghost h-8 px-3"
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          disabled={currentPage >= totalPages}
        >下一页</button>
      </div>
    </div>
  )
}


