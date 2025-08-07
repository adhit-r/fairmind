import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Bot, Play, Clock, CheckCircle } from "lucide-react"

export default function LLMTestingPage() {
  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">LLM Testing</h1>
          <p className="text-muted-foreground">
            Test Large Language Models for safety and compliance
          </p>
        </div>
        <Button>
          <Play className="mr-2 h-4 w-4" />
          New LLM Test
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>LLM Testing Suite</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            LLM testing configuration and results will be available here.
          </p>
        </CardContent>
      </Card>
    </div>
  )
} 