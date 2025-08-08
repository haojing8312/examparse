import React, { useCallback, useEffect, useState } from 'react'
import { invoke } from '@tauri-apps/api/core'

type EventPayload = {
  type: 'stage' | 'progress' | 'warning' | 'error' | 'metric' | 'completed'
  stage: string
  ts: string
  fileId: string
  message?: string | null
  percent?: number | null
}

export function App() {
  const [events, setEvents] = useState<EventPayload[]>([])

  const handleStartMock = useCallback(async () => {
    try {
      await invoke('start_mock')
    } catch (e) {
      console.error(e)
    }
  }, [])

  useEffect(() => {
    // 在 Tauri 中通过 window 事件收消息
    const handler = (e: any) => {
      try {
        const data = JSON.parse(e.payload) as EventPayload
        setEvents((prev) => [...prev, data])
      } catch {}
    }
    // @ts-ignore
    window.__TAURI__.event.listen('sidecar-event', handler)
    return () => {
      // @ts-ignore
      window.__TAURI__?.event?.unlisten?.('sidecar-event', handler)
    }
  }, [])

  return (
    <div style={{ padding: 24, fontFamily: 'Inter, system-ui, -apple-system, Segoe UI' }}>
      <h2>ExamParse Desktop</h2>
      <div style={{ marginBottom: 12 }}>
        <button onClick={handleStartMock}>开始 Mock 任务</button>
      </div>
      <div style={{ height: 360, overflow: 'auto', border: '1px solid #e5e5e5', padding: 12 }}>
        {events.map((e, i) => (
          <pre key={i} style={{ margin: 0 }}>{JSON.stringify(e)}</pre>
        ))}
      </div>
    </div>
  )
}


