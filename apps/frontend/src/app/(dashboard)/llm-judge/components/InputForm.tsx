'use client'

import { useState, useRef } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { IconUpload, IconLoader2, IconAlertTriangle } from '@tabler/icons-react'
import { JudgeModel } from '@/lib/api/hooks/useLLMJudge'

export interface InputFormProps {
  loading: boolean
  error: Error | null
  onEvaluate: (
    text: string,
    judgeModel: string,
    biasCategories: string[],
    targetModel: string
  ) => Promise<void>
  availableModels: JudgeModel[]
  availableCategories: string[]
}

export function InputForm({
  loading,
  error,
  onEvaluate,
  availableModels,
  availableCategories,
}: InputFormProps) {
  const [text, setText] = useState('')
  const [selectedJudge, setSelectedJudge] = useState('gpt-4-turbo')
  const [selectedCategories, setSelectedCategories] = useState<string[]>(['gender', 'race'])
  const [targetModel, setTargetModel] = useState('unknown')
  const [localError, setLocalError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // ========================================================================
  // Handlers
  // ========================================================================

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setLocalError(null)

    try {
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setLocalError('File size must be less than 10MB')
        return
      }

      // Handle text files
      if (file.type === 'text/plain' || file.name.endsWith('.txt')) {
        const content = await file.text()
        setText(content)
      } else {
        setLocalError('Only .txt files are supported. Please upload a text file.')
      }
    } catch (err) {
      setLocalError(
        err instanceof Error ? err.message : 'Failed to read file'
      )
    }
  }

  const handleCategoryToggle = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    )
  }

  const handleEvaluate = async () => {
    setLocalError(null)

    // Validation
    if (!text.trim()) {
      setLocalError('Please enter or upload text to evaluate')
      return
    }

    if (text.length > 50000) {
      setLocalError('Text must be 50,000 characters or less')
      return
    }

    if (selectedCategories.length === 0) {
      setLocalError('Please select at least one bias category')
      return
    }

    try {
      await onEvaluate(text, selectedJudge, selectedCategories, targetModel)
    } catch (err) {
      setLocalError(
        err instanceof Error ? err.message : 'Failed to evaluate bias'
      )
    }
  }

  const clearForm = () => {
    setText('')
    setLocalError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // ========================================================================
  // Render
  // ========================================================================

  const characterCount = text.length
  const maxCharacters = 50000
  const characterPercentage = (characterCount / maxCharacters) * 100

  return (
    <Card className="border-2 border-black shadow-brutal p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Evaluation Setup</h2>
        <p className="text-sm text-gray-600">
          Configure your bias evaluation settings and provide text to analyze
        </p>
      </div>

      {/* Errors */}
      {(error || localError) && (
        <Alert className="border-2 border-red-500 bg-red-50">
          <IconAlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {localError || error?.message}
          </AlertDescription>
        </Alert>
      )}

      {/* Text Input Section */}
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <Label htmlFor="text-input" className="text-base font-semibold">
            Text to Evaluate *
          </Label>
          <span className="text-xs text-gray-500">
            {characterCount.toLocaleString()} / {maxCharacters.toLocaleString()} characters
          </span>
        </div>

        <Textarea
          id="text-input"
          placeholder="Enter or paste the text you want to evaluate for bias..."
          value={text}
          onChange={(e) => {
            setText(e.target.value)
            setLocalError(null)
          }}
          disabled={loading}
          className="h-[200px] border-2 border-black font-mono text-sm resize-none"
        />

        {/* Character Count Progress */}
        <div className="w-full bg-gray-200 rounded-full h-2 border border-gray-300">
          <div
            className={`h-2 rounded-full transition-all ${
              characterPercentage > 100
                ? 'bg-red-500'
                : characterPercentage > 80
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(characterPercentage, 100)}%` }}
          />
        </div>

        {/* File Upload */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt"
          onChange={handleFileUpload}
          className="hidden"
          disabled={loading}
        />
        <Button
          type="button"
          variant="neutral"
          size="sm"
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          className="border-2 border-black w-full justify-center"
        >
          <IconUpload className="w-4 h-4 mr-2" />
          Upload .txt File
        </Button>
      </div>

      {/* Judge Model Selection */}
      <div className="space-y-3">
        <Label htmlFor="judge-model" className="text-base font-semibold">
          Judge Model *
        </Label>
        <Select value={selectedJudge} onValueChange={setSelectedJudge} disabled={loading}>
          <SelectTrigger id="judge-model" className="border-2 border-black font-semibold">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {availableModels.map((model) => (
              <SelectItem key={model.value} value={model.value}>
                {model.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs text-gray-600">
          The AI model that will evaluate your text for bias
        </p>
      </div>

      {/* Bias Categories Selection */}
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <Label className="text-base font-semibold">
            Bias Categories to Evaluate *
          </Label>
          <Button
            type="button"
            variant="noShadow"
            size="sm"
            onClick={() => setSelectedCategories(availableCategories)}
            disabled={loading}
            className="text-xs underline"
          >
            Select All
          </Button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {availableCategories.map((category) => (
            <div key={category} className="flex items-center space-x-2">
              <Checkbox
                id={`category-${category}`}
                checked={selectedCategories.includes(category)}
                onCheckedChange={() => handleCategoryToggle(category)}
                disabled={loading}
                className="border-2 border-black"
              />
              <Label
                htmlFor={`category-${category}`}
                className="text-sm font-medium cursor-pointer capitalize"
              >
                {category}
              </Label>
            </div>
          ))}
        </div>

        <p className="text-xs text-gray-600">
          Select which types of bias to evaluate. More categories = more comprehensive analysis
        </p>
      </div>

      {/* Target Model (Optional) */}
      <div className="space-y-3">
        <Label htmlFor="target-model" className="text-sm font-semibold">
          Target Model (Optional)
        </Label>
        <input
          id="target-model"
          type="text"
          placeholder="e.g., gpt-4, claude-3, unknown"
          value={targetModel}
          onChange={(e) => setTargetModel(e.target.value)}
          disabled={loading}
          className="w-full px-3 py-2 border-2 border-black rounded font-mono text-sm"
        />
        <p className="text-xs text-gray-600">
          The model whose outputs you&#39;re evaluating (for reference in results)
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 pt-4">
        <Button
          onClick={handleEvaluate}
          disabled={loading || !text.trim() || selectedCategories.length === 0}
          className="flex-1 border-2 border-black font-bold bg-black text-white hover:bg-gray-800"
        >
          {loading ? (
            <>
              <IconLoader2 className="w-4 h-4 mr-2 animate-spin" />
              Evaluating...
            </>
          ) : (
            'Start Evaluation'
          )}
        </Button>

        <Button
          onClick={clearForm}
          disabled={loading}
          variant="neutral"
          className="border-2 border-black font-bold"
        >
          Clear
        </Button>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border-2 border-blue-200 p-4 rounded">
        <p className="text-xs text-blue-900">
          <strong>💡 Tip:</strong> This evaluation sends your text to the selected judge model for bias analysis.
          The model will evaluate your text across the selected bias categories and provide detailed reasoning
          and recommendations.
        </p>
      </div>
    </Card>
  )
}
