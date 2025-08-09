import React, { useState, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { useToasts } from '@/components/ui/toast'

export type AppSettings = {
  openai_model: string
  openai_base_url: string
  ocr_enabled: boolean
  first_launch: boolean
}

type SettingsFormProps = {
  isWelcome?: boolean
  onComplete?: () => void
}

export function SettingsForm({ isWelcome = false, onComplete }: SettingsFormProps) {
  const [settings, setSettings] = useState<AppSettings>({
    openai_model: 'gpt-4o',
    openai_base_url: 'https://api.openai.com/v1',
    ocr_enabled: false,
    first_launch: true
  })
  const [apiKey, setApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const { push } = useToasts()

  const modelOptions = [
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
  ]

  useEffect(() => {
    const loadData = async () => {
      try {
        const [loadedSettings, loadedApiKey] = await Promise.all([
          invoke<AppSettings>('load_settings'),
          invoke<string>('load_api_key').catch(() => '')
        ])
        setSettings(loadedSettings)
        setApiKey(loadedApiKey || '')
      } catch (e) {
        console.error('Failed to load settings:', e)
      }
    }
    loadData()
  }, [])

  const validateForm = () => {
    const newErrors: Record<string, string> = {}
    
    if (!apiKey.trim()) {
      newErrors.apiKey = 'API Key 是必填项'
    } else if (!apiKey.startsWith('sk-')) {
      newErrors.apiKey = 'OpenAI API Key 应该以 sk- 开头'
    }
    
    if (!settings.openai_base_url.trim()) {
      newErrors.openai_base_url = 'API 基础 URL 是必填项'
    } else {
      try {
        new URL(settings.openai_base_url)
      } catch {
        newErrors.openai_base_url = '请输入有效的 URL'
      }
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSave = async () => {
    if (!validateForm()) return
    
    setLoading(true)
    try {
      const updatedSettings = { ...settings, first_launch: false }
      
      await Promise.all([
        invoke('save_settings', { settings: updatedSettings }),
        apiKey ? invoke('save_api_key', { apiKey }) : Promise.resolve()
      ])
      
      setSettings(updatedSettings)
      push({ title: '设置已保存', description: '配置已成功保存到系统' })
      
      if (onComplete) {
        onComplete()
      }
    } catch (e) {
      push({ title: '保存失败', description: String(e) })
    } finally {
      setLoading(false)
    }
  }

  const title = isWelcome ? '欢迎使用 ExamParse' : '设置'
  const subtitle = isWelcome ? '请配置 AI 服务以开始使用' : '管理您的应用设置'

  return (
    <Card className="mx-auto max-w-2xl">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <p className="text-sm text-muted-foreground">{subtitle}</p>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <Input
            type="password"
            label="OpenAI API Key"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            error={errors.apiKey}
          />
          
          <Input
            label="API 基础 URL"
            value={settings.openai_base_url}
            onChange={(e) => setSettings({ ...settings, openai_base_url: e.target.value })}
            placeholder="https://api.openai.com/v1"
            error={errors.openai_base_url}
          />
          
          <Select
            label="AI 模型"
            options={modelOptions}
            value={settings.openai_model}
            onChange={(value) => setSettings({ ...settings, openai_model: value })}
          />
          
          <Switch
            label="启用 OCR"
            description="对图片中的文字进行光学字符识别"
            checked={settings.ocr_enabled}
            onCheckedChange={(checked) => setSettings({ ...settings, ocr_enabled: checked })}
          />
        </div>
        
        <div className="flex justify-end gap-2 pt-4">
          {!isWelcome && (
            <Button 
              variant="ghost" 
              onClick={() => window.location.reload()}
              disabled={loading}
            >
              取消
            </Button>
          )}
          <Button 
            onClick={handleSave} 
            disabled={loading}
          >
            {loading ? '保存中...' : isWelcome ? '完成设置' : '保存设置'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}