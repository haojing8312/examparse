import React from 'react'
import * as RadixProgress from '@radix-ui/react-progress'

export function Progress({ value = 0 }: { value?: number }) {
  const clamped = Math.min(100, Math.max(0, value))
  return (
    <RadixProgress.Root className="relative h-2 w-full overflow-hidden rounded-full bg-white/10">
      <RadixProgress.Indicator
        className="h-full bg-primary transition-all"
        style={{ width: `${clamped}%` }}
      />
    </RadixProgress.Root>
  )
}


