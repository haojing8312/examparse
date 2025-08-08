import React from 'react'
import * as RadixDialog from '@radix-ui/react-dialog'
import { Button } from './button'

export function ConfirmDialog({
  open,
  title,
  description,
  onConfirm,
  onCancel,
}: {
  open: boolean
  title: string
  description?: string
  onConfirm: () => void
  onCancel: () => void
}) {
  return (
    <RadixDialog.Root open={open}>
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 bg-black/40" />
        <RadixDialog.Content className="card fixed left-1/2 top-1/2 w-[440px] -translate-x-1/2 -translate-y-1/2 p-4">
          <div className="mb-3">
            <RadixDialog.Title className="text-base font-semibold">{title}</RadixDialog.Title>
            {description && (
              <RadixDialog.Description className="mt-1 text-sm text-muted-foreground">
                {description}
              </RadixDialog.Description>
            )}
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={onCancel}>取消</Button>
            <Button onClick={onConfirm}>确定</Button>
          </div>
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  )
}


