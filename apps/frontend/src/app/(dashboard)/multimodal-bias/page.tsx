'use client'

import { useState } from 'react'
import { useMultimodalBias } from '@/lib/api/hooks/useMultimodalBias'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/hooks/use-toast'
import { IconPhoto, IconMusic, IconVideo, IconBrain, IconAlertTriangle, IconCheck } from '@tabler/icons-react'

export default function MultimodalBiasPage() {
  const { detectImageBias, detectAudioBias, detectVideoBias, detectCrossModalBias, loading, error } = useMultimodalBias()
  const { toast } = useToast()
  const [activeTab, setActiveTab] = useState('image')
  const [results, setResults] = useState<any[]>([])

  const [imageForm, setImageForm] = useState({
    modelOutputs: '',
  })

  const [audioForm, setAudioForm] = useState({
    modelOutputs: '',
  })

  const [videoForm, setVideoForm] = useState({
    modelOutputs: '',
  })

  const [crossModalForm, setCrossModalForm] = useState({
    modelOutputs: '',
    modalities: [] as string[],
  })

  const handleImageBias = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      let modelOutputs: any[] = []
      try {
        modelOutputs = JSON.parse(imageForm.modelOutputs)
      } catch {
        throw new Error('Invalid JSON format for model outputs')
      }

      const result = await detectImageBias({ model_outputs: modelOutputs })
      setResults(result)
      toast({
        title: "Image bias detection completed",
        description: "Image bias analysis has been completed successfully.",
      })
    } catch (err) {
      toast({
        title: "Detection failed",
        description: err instanceof Error ? err.message : "An error occurred",
        variant: "destructive",
      })
    }
  }

  const handleAudioBias = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      let modelOutputs: any[] = []
      try {
        modelOutputs = JSON.parse(audioForm.modelOutputs)
      } catch {
        throw new Error('Invalid JSON format for model outputs')
      }

      const result = await detectAudioBias({ model_outputs: modelOutputs })
      setResults(result)
      toast({
        title: "Audio bias detection completed",
        description: "Audio bias analysis has been completed successfully.",
      })
    } catch (err) {
      toast({
        title: "Detection failed",
        description: err instanceof Error ? err.message : "An error occurred",
        variant: "destructive",
      })
    }
  }

  const handleVideoBias = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      let modelOutputs: any[] = []
      try {
        modelOutputs = JSON.parse(videoForm.modelOutputs)
      } catch {
        throw new Error('Invalid JSON format for model outputs')
      }

      const result = await detectVideoBias({ model_outputs: modelOutputs })
      setResults(result)
      toast({
        title: "Video bias detection completed",
        description: "Video bias analysis has been completed successfully.",
      })
    } catch (err) {
      toast({
        title: "Detection failed",
        description: err instanceof Error ? err.message : "An error occurred",
        variant: "destructive",
      })
    }
  }

  const handleCrossModalBias = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      let modelOutputs: any[] = []
      try {
        modelOutputs = JSON.parse(crossModalForm.modelOutputs)
      } catch {
        throw new Error('Invalid JSON format for model outputs')
      }

      if (crossModalForm.modalities.length === 0) {
        throw new Error('Please select at least one modality')
      }

      const result = await detectCrossModalBias({
        model_outputs: modelOutputs,
        modalities: crossModalForm.modalities,
      })
      setResults(result)
      toast({
        title: "Cross-modal bias detection completed",
        description: "Cross-modal bias analysis has been completed successfully.",
      })
    } catch (err) {
      toast({
        title: "Detection failed",
        description: err instanceof Error ? err.message : "An error occurred",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold">Multimodal Bias Detection</h1>
        <p className="text-muted-foreground mt-1">
          Detect bias in image, audio, video, and cross-modal AI models
        </p>
      </div>

      {error && (
        <Alert className="border-2 border-red-500 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="border-2 border-black">
          <TabsTrigger value="image" className="border-r-2 border-black">
            <IconPhoto className="mr-2 h-4 w-4" />
            Image
          </TabsTrigger>
          <TabsTrigger value="audio" className="border-r-2 border-black">
            <IconMusic className="mr-2 h-4 w-4" />
            Audio
          </TabsTrigger>
          <TabsTrigger value="video" className="border-r-2 border-black">
            <IconVideo className="mr-2 h-4 w-4" />
            Video
          </TabsTrigger>
          <TabsTrigger value="cross-modal">
            <IconBrain className="mr-2 h-4 w-4" />
            Cross-Modal
          </TabsTrigger>
        </TabsList>

        <TabsContent value="image" className="space-y-4">
          <Card className="p-6 border-2 border-black shadow-brutal">
            <h2 className="text-2xl font-bold mb-4">Image Bias Detection</h2>
            <form onSubmit={handleImageBias} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="imageOutputs">Model Outputs (JSON) *</Label>
                <Textarea
                  id="imageOutputs"
                  value={imageForm.modelOutputs}
                  onChange={(e) => setImageForm({ ...imageForm, modelOutputs: e.target.value })}
                  placeholder='[{"text": "prompt", "image_url": "https://...", "metadata": {}}]'
                  required
                  className="border-2 border-black font-mono text-sm"
                  rows={8}
                />
              </div>
              <Button type="submit" variant="default" disabled={loading} className="w-full">
                {loading ? 'Detecting Bias...' : 'Detect Image Bias'}
              </Button>
            </form>
          </Card>
        </TabsContent>

        <TabsContent value="audio" className="space-y-4">
          <Card className="p-6 border-2 border-black shadow-brutal">
            <h2 className="text-2xl font-bold mb-4">Audio Bias Detection</h2>
            <form onSubmit={handleAudioBias} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="audioOutputs">Model Outputs (JSON) *</Label>
                <Textarea
                  id="audioOutputs"
                  value={audioForm.modelOutputs}
                  onChange={(e) => setAudioForm({ ...audioForm, modelOutputs: e.target.value })}
                  placeholder='[{"text": "prompt", "audio_url": "https://...", "metadata": {}}]'
                  required
                  className="border-2 border-black font-mono text-sm"
                  rows={8}
                />
              </div>
              <Button type="submit" variant="default" disabled={loading} className="w-full">
                {loading ? 'Detecting Bias...' : 'Detect Audio Bias'}
              </Button>
            </form>
          </Card>
        </TabsContent>

        <TabsContent value="video" className="space-y-4">
          <Card className="p-6 border-2 border-black shadow-brutal">
            <h2 className="text-2xl font-bold mb-4">Video Bias Detection</h2>
            <form onSubmit={handleVideoBias} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="videoOutputs">Model Outputs (JSON) *</Label>
                <Textarea
                  id="videoOutputs"
                  value={videoForm.modelOutputs}
                  onChange={(e) => setVideoForm({ ...videoForm, modelOutputs: e.target.value })}
                  placeholder='[{"text": "prompt", "video_url": "https://...", "metadata": {}}]'
                  required
                  className="border-2 border-black font-mono text-sm"
                  rows={8}
                />
              </div>
              <Button type="submit" variant="default" disabled={loading} className="w-full">
                {loading ? 'Detecting Bias...' : 'Detect Video Bias'}
              </Button>
            </form>
          </Card>
        </TabsContent>

        <TabsContent value="cross-modal" className="space-y-4">
          <Card className="p-6 border-2 border-black shadow-brutal">
            <h2 className="text-2xl font-bold mb-4">Cross-Modal Bias Detection</h2>
            <form onSubmit={handleCrossModalBias} className="space-y-4">
              <div className="space-y-2">
                <Label>Modalities *</Label>
                <div className="grid grid-cols-2 gap-2">
                  {['image', 'audio', 'video', 'text'].map((modality) => (
                    <div key={modality} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id={modality}
                        checked={crossModalForm.modalities.includes(modality)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setCrossModalForm({
                              ...crossModalForm,
                              modalities: [...crossModalForm.modalities, modality],
                            })
                          } else {
                            setCrossModalForm({
                              ...crossModalForm,
                              modalities: crossModalForm.modalities.filter(m => m !== modality),
                            })
                          }
                        }}
                        className="border-2 border-black"
                      />
                      <Label htmlFor={modality} className="font-normal capitalize">{modality}</Label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="crossModalOutputs">Model Outputs (JSON) *</Label>
                <Textarea
                  id="crossModalOutputs"
                  value={crossModalForm.modelOutputs}
                  onChange={(e) => setCrossModalForm({ ...crossModalForm, modelOutputs: e.target.value })}
                  placeholder='[{"text": "...", "image_url": "...", "audio_url": "...", "video_url": "...", "metadata": {}}]'
                  required
                  className="border-2 border-black font-mono text-sm"
                  rows={8}
                />
              </div>
              <Button type="submit" variant="default" disabled={loading} className="w-full">
                {loading ? 'Detecting Bias...' : 'Detect Cross-Modal Bias'}
              </Button>
            </form>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Results */}
      {results.length > 0 && (
        <Card className="p-6 border-2 border-black shadow-brutal">
          <h2 className="text-2xl font-bold mb-4">Detection Results</h2>
          <div className="space-y-3">
            {results.map((result, index) => (
              <div key={index} className="p-4 border-2 border-black bg-white">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="font-medium capitalize">{result.modality} - {result.biasType}</span>
                    <Badge 
                      variant={result.isBiased ? 'destructive' : 'default'} 
                      className="ml-2 border-2 border-black"
                    >
                      {result.isBiased ? 'Biased' : 'Not Biased'}
                    </Badge>
                  </div>
                  <Badge variant={result.biasScore > 0.7 ? 'destructive' : result.biasScore > 0.5 ? 'secondary' : 'default'} className="border-2 border-black">
                    {(result.biasScore * 100).toFixed(1)}%
                  </Badge>
                </div>
                <div className="text-sm text-muted-foreground mb-2">
                  Confidence: {(result.confidence * 100).toFixed(1)}%
                </div>
                {result.recommendations && result.recommendations.length > 0 && (
                  <div className="mt-2">
                    <Label className="text-sm font-medium">Recommendations:</Label>
                    <ul className="list-disc list-inside text-sm text-muted-foreground">
                      {result.recommendations.map((rec: string, i: number) => (
                        <li key={i}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

