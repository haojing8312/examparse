import React from 'react'
import { twMerge } from 'tailwind-merge'

export type Column<T> = {
  key: keyof T
  title: string
  render?: (value: any, row: T) => React.ReactNode
}

export function SimpleTable<T extends { id?: React.Key }>(
  { columns, data, className }: { columns: Column<T>[]; data: T[]; className?: string }
) {
  return (
    <div className={twMerge('overflow-auto rounded-lg border border-border', className)}>
      <table className="w-full text-sm">
        <thead className="bg-white/5">
          <tr>
            {columns.map((c) => (
              <th key={String(c.key)} className="px-3 py-2 text-left font-medium text-muted-foreground">{c.title}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={row.id ?? i} className="border-t border-border/60">
              {columns.map((c) => {
                const value = row[c.key]
                return (
                  <td key={String(c.key)} className="px-3 py-2">
                    {c.render ? c.render(value, row) : String(value)}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}


