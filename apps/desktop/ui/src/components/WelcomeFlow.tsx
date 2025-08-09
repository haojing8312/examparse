import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { SettingsForm } from './SettingsForm'

type WelcomeStep = 'intro' | 'settings' | 'complete'

type WelcomeFlowProps = {
  onComplete: () => void
}

export function WelcomeFlow({ onComplete }: WelcomeFlowProps) {
  const [step, setStep] = useState<WelcomeStep>('intro')

  const renderIntro = () => (
    <motion.div
      key="intro"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="text-center"
    >
      <Card className="mx-auto max-w-2xl">
        <CardContent className="py-12">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-foreground mb-4">
              欢迎使用 ExamParse
            </h1>
            <p className="text-lg text-muted-foreground mb-6">
              智能试题解析工具，将 PDF/Word 试题转换为结构化 Excel 格式
            </p>
          </div>
          
          <div className="grid gap-6 text-left max-w-lg mx-auto">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-primary font-semibold text-sm">1</span>
              </div>
              <div>
                <h3 className="font-medium text-foreground mb-1">AI 智能解析</h3>
                <p className="text-sm text-muted-foreground">
                  使用 OpenAI 等 AI 服务智能识别和分类试题类型
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-primary font-semibold text-sm">2</span>
              </div>
              <div>
                <h3 className="font-medium text-foreground mb-1">多格式支持</h3>
                <p className="text-sm text-muted-foreground">
                  支持 PDF、Word 文档，自动识别单选、多选、判断、简答等题型
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-primary font-semibold text-sm">3</span>
              </div>
              <div>
                <h3 className="font-medium text-foreground mb-1">结构化输出</h3>
                <p className="text-sm text-muted-foreground">
                  生成标准化 Excel 文件，便于后续编辑和管理
                </p>
              </div>
            </div>
          </div>
          
          <div className="mt-8">
            <Button size="lg" onClick={() => setStep('settings')}>
              开始配置
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )

  const renderSettings = () => (
    <motion.div
      key="settings"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <SettingsForm 
        isWelcome 
        onComplete={() => setStep('complete')} 
      />
    </motion.div>
  )

  const renderComplete = () => (
    <motion.div
      key="complete"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="text-center"
    >
      <Card className="mx-auto max-w-2xl">
        <CardContent className="py-12">
          <div className="mb-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-foreground mb-2">
              配置完成！
            </h2>
            <p className="text-muted-foreground">
              您现在可以开始使用 ExamParse 处理试题文件了
            </p>
          </div>
          
          <Button size="lg" onClick={onComplete}>
            进入应用
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  )

  const steps = {
    intro: renderIntro(),
    settings: renderSettings(),
    complete: renderComplete()
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      {steps[step]}
    </div>
  )
}