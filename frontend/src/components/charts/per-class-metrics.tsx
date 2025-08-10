"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface PerClassMetricsProps {
  perClass?: {
    [className: string]: {
      precision: number
      recall: number
      f1: number
    }
  }
}

export function PerClassMetrics({ perClass }: PerClassMetricsProps) {
  if (!perClass || Object.keys(perClass).length === 0) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-mono">PER_CLASS_METRICS</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center text-muted-foreground">
            No per-class metrics available.
          </div>
        </CardContent>
      </Card>
    )
  }

  const classes = Object.keys(perClass)
  const metrics = ['precision', 'recall', 'f1'] as const

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-mono">PER_CLASS_METRICS</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {classes.map((className) => (
            <div key={className} className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">
                Class: {className}
              </div>
              <div className="grid grid-cols-3 gap-2">
                {metrics.map((metric) => {
                  const value = perClass[className][metric]
                  const percentage = Math.round(value * 100)
                  
                  return (
                    <div key={metric} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-muted-foreground uppercase">{metric}</span>
                        <span className="font-mono">{percentage}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-gray-800 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-4 pt-4 border-t">
          <div className="grid grid-cols-3 gap-4 text-xs text-muted-foreground">
            {metrics.map((metric) => (
              <div key={metric} className="text-center">
                <div className="font-medium uppercase">{metric}</div>
                <div className="font-mono">
                  {Math.round(
                    Object.values(perClass).reduce((sum, classMetrics) => 
                      sum + classMetrics[metric], 0
                    ) / classes.length * 100
                  )}%
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
