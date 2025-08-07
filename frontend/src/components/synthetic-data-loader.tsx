'use client'

import { useDemo } from '@/contexts/DemoContext'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Database, BarChart3, TrendingUp, AlertTriangle } from 'lucide-react'

export function SyntheticDataLoader() {
  const { hasSyntheticData, loadSyntheticData } = useDemo()

  if (hasSyntheticData) {
    return null
  }

  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mb-4">
            <Database className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-2xl font-bold">Welcome to Fairmind Demo</CardTitle>
          <p className="text-muted-foreground mt-2">
            This is a demonstration of Fairmind's AI governance and bias detection platform.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-center space-x-3 text-sm">
              <BarChart3 className="w-4 h-4 text-blue-500" />
              <span>Advanced Bias Detection (SHAP, LIME)</span>
            </div>
            <div className="flex items-center space-x-3 text-sm">
              <TrendingUp className="w-4 h-4 text-green-500" />
              <span>Real-time Model Monitoring</span>
            </div>
            <div className="flex items-center space-x-3 text-sm">
              <AlertTriangle className="w-4 h-4 text-orange-500" />
              <span>Knowledge Graph Analysis</span>
            </div>
          </div>
          
          <Button 
            onClick={loadSyntheticData}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
          >
            Load Demo Data
          </Button>
          
          <p className="text-xs text-center text-muted-foreground">
            Click to load synthetic data and explore the platform features
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
