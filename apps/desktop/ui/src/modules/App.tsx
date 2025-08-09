import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { open } from '@tauri-apps/plugin-dialog'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { SimpleTable, type Column } from '@/components/ui/table'
import { ToastViewport, ToastItem, useToasts } from '@/components/ui/toast'
import { ConfirmDialog } from '@/components/ui/dialog'
import { WelcomeFlow } from '@/components/WelcomeFlow'
import { SettingsForm, type AppSettings } from '@/components/SettingsForm'

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
  const [settings, setSettings] = useState<AppSettings | null>(null)
  const [showWelcome, setShowWelcome] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const { toasts, push, remove } = useToasts()
  const [errorOpen, setErrorOpen] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string>('')

  useEffect(() => {
    const loadInitialSettings = async () => {
      try {
        const loadedSettings = await invoke<AppSettings>('load_settings')
        setSettings(loadedSettings)
        
        if (loadedSettings.first_launch) {
          setShowWelcome(true)
        }
      } catch (e) {
        console.error('Failed to load settings:', e)
        setShowWelcome(true)
      }
    }
    loadInitialSettings()
  }, [])

  const handleStartMock = useCallback(async () => {
    try {
      await invoke('start_mock')
      push({ title: '已触发 Mock 任务' })
    } catch (e) {
      console.error(e)
      push({ title: '操作失败', description: String(e) })
    }
  }, [push])

  const handlePickFiles = useCallback(async () => {
    const selection = await open({ multiple: true, filters: [{ name: 'PDF', extensions: ['pdf'] }] })
    if (!selection) return
    const paths = Array.isArray(selection) ? selection : [selection]
    const uniq = Array.from(new Set(paths as string[]))
    setFiles(uniq)
    push({ title: '已选择文件', description: `${uniq.length} 个` })
  }, [push])

  const handlePickOutput = useCallback(async () => {
    const dir = await open({ directory: true })
    if (typeof dir === 'string') setOutputDir(dir)
    if (typeof dir === 'string') push({ title: '已设置输出目录', description: dir })
  }, [push])

  const handleStartJobs = useCallback(async () => {
    if (files.length === 0) return
    try {
      await invoke('start_jobs', { inputs: files, output_dir: outputDir ?? undefined })
      push({ title: '任务已开始', description: `${files.length} 个文件` })
    } catch (e) {
      console.error(e)
      push({ title: '任务启动失败', description: String(e) })
    }
  }, [files, outputDir, push])

  useEffect(() => {
    let unlisten: null | (() => void) = null
    listen<string>('sidecar-event', (e) => {
      try {
        const data = JSON.parse(e.payload) as EventPayload
        setEvents((prev) => [...prev, data])
        if (data.type === 'error') {
          setErrorMsg(data.message ?? '未知错误')
          setErrorOpen(true)
        }
      } catch {}
    }).then((fn) => (unlisten = fn))
    return () => {
      if (unlisten) unlisten()
    }
  }, [])

  const globalPercent = useMemo(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const p = events[i].percent
      if (typeof p === 'number' && !Number.isNaN(p)) {
        return p <= 1 ? p * 100 : p
      }
    }
    return undefined
  }, [events])

  const handleCopyLogs = useCallback(async () => {
    try {
      const text = events.map((e) => JSON.stringify(e)).join('\n')
      await navigator.clipboard.writeText(text)
      push({ title: '日志已复制' })
    } catch (e) {
      push({ title: '复制失败', description: String(e) })
    }
  }, [events, push])

  const handleWelcomeComplete = useCallback(() => {
    setShowWelcome(false)
    window.location.reload()
  }, [])

  const handleSettingsComplete = useCallback(() => {
    setShowSettings(false)
    window.location.reload()
  }, [])

  const columns = useMemo<Column<(EventPayload & { id: number })>[]>(
    () => [
      { key: 'ts', title: '时间' },
      { key: 'stage', title: '阶段' },
      { key: 'type', title: '类型' },
      {
        key: 'percent',
        title: '进度',
        render: (v) => {
          if (typeof v !== 'number' || Number.isNaN(v)) return '-'
          const value = v <= 1 ? v * 100 : v
          return <Progress value={value} />
        }
      },
      { key: 'message', title: '信息', render: (v) => (v ? <span className="text-xs text-muted-foreground">{v}</span> : '-') },
    ],
    []
  )

  if (showWelcome) {
    return (
      <div>
        <WelcomeFlow onComplete={handleWelcomeComplete} />
        <ToastViewport>
          {toasts.map((t) => (
            <ToastItem key={t.id} toast={t} onClose={() => remove(t.id)} />
          ))}
        </ToastViewport>
      </div>
    )
  }

  if (showSettings) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <SettingsForm onComplete={handleSettingsComplete} />
        <ToastViewport>
          {toasts.map((t) => (
            <ToastItem key={t.id} toast={t} onClose={() => remove(t.id)} />
          ))}
        </ToastViewport>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-2xl font-semibold">ExamParse Desktop</h2>
        <Button variant="ghost" onClick={() => setShowSettings(true)}>
          设置
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-1">
          <CardHeader>
            <CardTitle>控制台</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              <Button onClick={handleStartMock}>开始 Mock 任务</Button>
              <Button variant="secondary" onClick={handlePickFiles}>选择 PDF</Button>
              <Button variant="ghost" onClick={handlePickOutput}>选择输出目录</Button>
              <Button onClick={handleStartJobs} disabled={files.length === 0}>开始处理</Button>
            </div>
            <div className="mt-3">
              <div className="mb-2 text-sm text-muted-foreground">阶段进度</div>
              <Progress value={typeof globalPercent === 'number' ? globalPercent : 0} />
            </div>
            <div className="mt-3 space-y-1 text-sm text-muted-foreground">
              <div>
                已选文件：{files.length > 0 ? <span className="text-foreground">{files.length} 个</span> : '未选择'}
              </div>
              <div>输出目录：{outputDir ?? '未设置（将使用默认）'}</div>
            </div>
            <div className="mt-3">
              <Button variant="ghost" onClick={handleCopyLogs}>复制日志</Button>
            </div>
          </CardContent>
        </Card>

        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }} className="xl:col-span-2">
          <Card className="h-[420px]">
            <CardHeader>
              <CardTitle>事件流</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid h-[340px] grid-cols-2 gap-4 overflow-auto">
                <div className="col-span-2 xl:col-span-1">
                  <SimpleTable
                    columns={columns}
                    data={events.map((e, i) => ({ ...e, id: i }))}
                  />
                </div>
                <div className="col-span-2 xl:col-span-1">
                  <div className="relative ml-2 border-l border-border/50 pl-4">
                    {events.length === 0 && (
                      <div className="text-sm text-muted-foreground">暂无事件</div>
                    )}
                    {events.map((e, i) => (
                      <div key={i} className="relative mb-3">
                        <div className="absolute -left-2 top-1 h-2 w-2 -translate-x-1/2 rounded-full bg-primary" />
                        <div className="text-xs text-muted-foreground">{e.ts}</div>
                        <div className="text-sm">
                          [{e.type}] {e.stage}
                          {e.message ? <span className="text-muted-foreground"> - {e.message}</span> : null}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <ConfirmDialog
        open={errorOpen}
        title="发生错误"
        description={errorMsg}
        onCancel={() => setErrorOpen(false)}
        onConfirm={() => {
          setErrorOpen(false)
          handleCopyLogs()
        }}
      />

      <ToastViewport>
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onClose={() => remove(t.id)} />
        ))}
      </ToastViewport>
    </div>
  )
}


