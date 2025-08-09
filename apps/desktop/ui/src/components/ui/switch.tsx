import React from 'react'
import { twMerge } from 'tailwind-merge'

export type SwitchProps = {
  checked?: boolean
  onCheckedChange?: (checked: boolean) => void
  label?: string
  description?: string
  disabled?: boolean
  className?: string
}

export const Switch = React.forwardRef<HTMLButtonElement, SwitchProps>(
  ({ checked = false, onCheckedChange, label, description, disabled = false, className }, ref) => (
    <div className={twMerge('flex items-center justify-between', className)}>
      <div className="space-y-0.5">
        {label && <div className="text-sm font-medium text-foreground">{label}</div>}
        {description && <div className="text-xs text-muted-foreground">{description}</div>}
      </div>
      <button
        ref={ref}
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onCheckedChange?.(!checked)}
        className={twMerge(
          'inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent bg-muted transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
          checked && 'bg-primary',
          disabled && 'cursor-not-allowed opacity-50'
        )}
      >
        <span
          className={twMerge(
            'pointer-events-none block h-4 w-4 rounded-full bg-white shadow-lg ring-0 transition-transform',
            checked ? 'translate-x-4' : 'translate-x-0'
          )}
        />
      </button>
    </div>
  )
)
Switch.displayName = 'Switch'