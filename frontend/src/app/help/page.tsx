import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { HelpCircle } from "lucide-react"

export default function HelpPage() {
  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Help & Support</h1>
        <p className="text-muted-foreground">
          Get help and support for the FairMind platform
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Documentation</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Help documentation and support resources will be available here.
          </p>
        </CardContent>
      </Card>
    </div>
  )
} 