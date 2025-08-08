import React from 'react'
import { twMerge } from 'tailwind-merge'

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={twMerge('card p-4', className)} {...props} />
}

export function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={twMerge('mb-3 flex items-center justify-between', className)} {...props} />
}

export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={twMerge('text-base font-semibold', className)} {...props} />
}

export function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={twMerge('text-sm', className)} {...props} />
}


