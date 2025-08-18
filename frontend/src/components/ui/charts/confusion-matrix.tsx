"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface ConfusionMatrixProps {
  matrix?: number[][]
  labels?: string[]
}

export function ConfusionMatrix({ matrix, labels }: ConfusionMatrixProps) {
  if (!matrix || !labels) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-mono">CONFUSION_MATRIX</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center text-muted-foreground">
            No confusion matrix data available.
          </div>
        </CardContent>
      </Card>
    )
  }

  const maxValue = Math.max(...matrix.flat())
  const minValue = Math.min(...matrix.flat())

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-mono">CONFUSION_MATRIX</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="grid grid-cols-[auto_1fr] gap-2 text-xs">
            <div className="text-muted-foreground">Predicted →</div>
            <div className="grid grid-cols-2 gap-1">
              {labels.map((label, i) => (
                <div key={i} className="text-center font-medium text-muted-foreground">
                  {label}
                </div>
              ))}
            </div>
          </div>
          
          {matrix.map((row, rowIndex) => (
            <div key={rowIndex} className="grid grid-cols-[auto_1fr] gap-2 text-xs">
              <div className="flex items-center justify-end pr-2 font-medium text-muted-foreground">
                {rowIndex === 0 && <span className="rotate-90 transform origin-center">Actual</span>}
                <span className="ml-2">{labels[rowIndex]}</span>
              </div>
              <div className="grid grid-cols-2 gap-1">
                {row.map((value, colIndex) => {
                  const normalizedValue = (value - minValue) / (maxValue - minValue)
                  const intensity = Math.round(normalizedValue * 255)
                  const bgColor = `bg-gray-${Math.max(100, Math.min(900, Math.round(normalizedValue * 800 + 100)))}`
                  
                  return (
                    <div
                      key={colIndex}
                      className={`
                        p-2 text-center font-mono text-xs border
                        ${bgColor} 
                        ${normalizedValue > 0.5 ? 'text-white' : 'text-gray-900'}
                      `}
                      style={{
                        backgroundColor: `rgb(${255 - intensity}, ${255 - intensity}, ${255 - intensity})`,
                        color: intensity > 127 ? 'white' : 'black'
                      }}
                    >
                      {value}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-4 pt-4 border-t">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Min: {minValue}</span>
            <span>Max: {maxValue}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
