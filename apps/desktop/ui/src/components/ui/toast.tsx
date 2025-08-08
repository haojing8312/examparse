import React, { useEffect, useState } from 'react'
import * as RadixToast from '@radix-ui/react-toast'

type Toast = { id: number; title?: string; description?: string }

export function useToasts() {
  const [toasts, setToasts] = useState<Toast[]>([])
  const push = (t: Omit<Toast, 'id'>) => setToasts((s) => [...s, { id: Date.now(), ...t }])
  const remove = (id: number) => setToasts((s) => s.filter((x) => x.id !== id))
  return { toasts, push, remove }
}

export function ToastViewport({ children }: { children?: React.ReactNode }) {
  const [openIds, setOpenIds] = useState<number[]>([])
  useEffect(() => {
    setOpenIds((ids) => ids)
  }, [])
  return (
    <RadixToast.Provider swipeDirection="right">
      {children}
      <RadixToast.Viewport className="fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2" />
    </RadixToast.Provider>
  )
}

export function ToastItem({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  return (
    <RadixToast.Root className="card p-3">
      {toast.title && <RadixToast.Title className="font-medium">{toast.title}</RadixToast.Title>}
      {toast.description && (
        <RadixToast.Description className="text-sm text-muted-foreground">
          {toast.description}
        </RadixToast.Description>
      )}
      <RadixToast.Close asChild>
        <button className="btn btn-ghost mt-2 h-8 px-3" onClick={onClose}>关闭</button>
      </RadixToast.Close>
    </RadixToast.Root>
  )
}


