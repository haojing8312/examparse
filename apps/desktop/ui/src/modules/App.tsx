import React, { useCallback, useEffect, useState } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { open } from '@tauri-apps/plugin-dialog'

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
  const [files, setFiles] = useState<string[]>([])
  const [outputDir, setOutputDir] = useState<string | null>(null)

  const handleStartMock = useCallback(async () => {
    try {
      await invoke('start_mock')
    } catch (e) {
      console.error(e)
    }
  }, [])

  const handlePickFiles = useCallback(async () => {
    const selection = await open({ multiple: true, filters: [{ name: 'PDF', extensions: ['pdf'] }] })
    if (!selection) return
    const paths = Array.isArray(selection) ? selection : [selection]
    setFiles(paths as string[])
  }, [])

  const handlePickOutput = useCallback(async () => {
    const dir = await open({ directory: true })
    if (typeof dir === 'string') setOutputDir(dir)
  }, [])

  const handleStartJobs = useCallback(async () => {
    if (files.length === 0) return
    try {
      await invoke('start_jobs', { inputs: files, output_dir: outputDir ?? undefined })
    } catch (e) {
      console.error(e)
    }
  }, [files, outputDir])

  useEffect(() => {
    let unlisten: null | (() => void) = null
    listen<string>('sidecar-event', (e) => {
      try {
        const data = JSON.parse(e.payload) as EventPayload
        setEvents((prev) => [...prev, data])
      } catch {}
    }).then((fn) => (unlisten = fn))
    return () => {
      if (unlisten) unlisten()
    }
  }, [])

  return (
    <div style={{ padding: 24, fontFamily: 'Inter, system-ui, -apple-system, Segoe UI' }}>
      <h2>ExamParse Desktop</h2>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <button onClick={handleStartMock}>开始 Mock 任务</button>
        <button onClick={handlePickFiles}>选择 PDF</button>
        <button onClick={handlePickOutput}>选择输出目录</button>
        <button onClick={handleStartJobs} disabled={files.length === 0}>开始处理</button>
      </div>
      <div style={{ marginBottom: 12, color: '#666' }}>
        <div>已选文件：{files.length > 0 ? files.join(', ') : '未选择'}</div>
        <div>输出目录：{outputDir ?? '未设置（将使用默认）'}</div>
      </div>
      <div style={{ height: 360, overflow: 'auto', border: '1px solid #e5e5e5', padding: 12 }}>
        {events.map((e, i) => (
          <pre key={i} style={{ margin: 0 }}>{JSON.stringify(e)}</pre>
        ))}
      </div>
    </div>
  )
}


