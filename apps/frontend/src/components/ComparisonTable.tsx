import React from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Check, X, AlertTriangle, Minus } from "lucide-react"

const ComparisonTable = () => {
  const data = [
    {
      feature: "Fairness Metrics",
      fairmind: { text: "Listed but not implemented", status: "warning" },
      ibm: { text: "Full library", status: "success" },
      aws: { text: "Full library", status: "success" },
      arize: { text: "Full library", status: "success" },
    },
    {
      feature: "UI/UX",
      fairmind: { text: "Modern, well-designed", status: "success" },
      ibm: { text: "CLI/notebook only", status: "error" },
      aws: { text: "Good", status: "success" },
      arize: { text: "Excellent", status: "success" },
    },
    {
      feature: "Model Agnostic",
      fairmind: { text: "Yes", status: "success" },
      ibm: { text: "Partial", status: "warning" },
      aws: { text: "Yes", status: "success" },
      arize: { text: "Yes", status: "success" },
    },
    {
      feature: "Compliance Focus",
      fairmind: { text: "Strong", status: "success" },
      ibm: { text: "None", status: "error" },
      aws: { text: "Basic", status: "warning" },
      arize: { text: "Strong", status: "success" },
    },
    {
      feature: "Continuous Monitoring",
      fairmind: { text: "Planned but not implemented", status: "warning" },
      ibm: { text: "None", status: "error" },
      aws: { text: "Yes", status: "success" },
      arize: { text: "Excellent", status: "success" },
    },
    {
      feature: "Explainability",
      fairmind: { text: "Missing", status: "error" },
      ibm: { text: "None", status: "error" },
      aws: { text: "SHAP integration", status: "success" },
      arize: { text: "Built-in", status: "success" },
    },
    {
      feature: "Mitigation",
      fairmind: { text: "Missing", status: "error" },
      ibm: { text: "Multiple algorithms", status: "success" },
      aws: { text: "Basic", status: "warning" },
      arize: { text: "Recommendations only", status: "warning" },
    },
  ]

  const getIcon = (status: string) => {
    switch (status) {
      case "success":
        return <Check className="h-4 w-4 text-green-600 mr-2 inline-block" />
      case "warning":
        return <AlertTriangle className="h-4 w-4 text-yellow-600 mr-2 inline-block" />
      case "error":
        return <X className="h-4 w-4 text-red-600 mr-2 inline-block" />
      default:
        return <Minus className="h-4 w-4 text-gray-400 mr-2 inline-block" />
    }
  }

  return (
    <Card className="w-full max-w-5xl mx-auto my-12">
      <CardHeader>
        <CardTitle className="text-3xl text-center">FairMind vs. The Competition</CardTitle>
        <CardDescription className="text-center text-lg mt-2">
          See how FairMind stacks up against other AI fairness and monitoring tools.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[200px] font-bold text-lg">Feature</TableHead>
              <TableHead className="font-bold text-lg bg-orange-50 text-orange-900 border-l-2 border-r-2 border-orange-200">FairMind (Current)</TableHead>
              <TableHead className="font-bold text-lg">IBM AIF360</TableHead>
              <TableHead className="font-bold text-lg">AWS Clarify</TableHead>
              <TableHead className="font-bold text-lg">Arize AI</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((row, index) => (
              <TableRow key={index}>
                <TableCell className="font-medium">{row.feature}</TableCell>
                <TableCell className="bg-orange-50 border-l-2 border-r-2 border-orange-200">
                  <div className="flex items-center">
                    {getIcon(row.fairmind.status)}
                    <span>{row.fairmind.text}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center">
                    {getIcon(row.ibm.status)}
                    <span>{row.ibm.text}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center">
                    {getIcon(row.aws.status)}
                    <span>{row.aws.text}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center">
                    {getIcon(row.arize.status)}
                    <span>{row.arize.text}</span>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

export default ComparisonTable
