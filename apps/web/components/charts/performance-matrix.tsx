"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@fairmind/ui"

const confusionMatrix = [
  [847, 23, 12, 8],
  [31, 756, 18, 15],
  [19, 22, 689, 24],
  [14, 19, 31, 712],
]

const labels = ["APPROVED", "DENIED", "PENDING", "REVIEW"]

export function PerformanceMatrix() {
  const total = confusionMatrix.flat().reduce((a, b) => a + b, 0)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">CONFUSION_MATRIX</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-5 gap-1 text-xs">
          <div></div>
          {labels.map((label) => (
            <div key={label} className="text-center font-bold p-2">
              {label}
            </div>
          ))}
          {confusionMatrix.map((row, i) => (
            <>
              <div key={`label-${i}`} className="font-bold p-2 text-right">
                {labels[i]}
              </div>
              {row.map((value, j) => (
                <div
                  key={`cell-${i}-${j}`}
                  className={`p-2 text-center border ${i === j ? "bg-white text-black" : "bg-muted"}`}
                >
                  {value}
                </div>
              ))}
            </>
          ))}
        </div>
        <div className="mt-4 text-xs text-muted-foreground">TOTAL_PREDICTIONS: {total.toLocaleString()}</div>
      </CardContent>
    </Card>
  )
}
