import { AITimeTravel } from "@/components/ai-time-travel"

export default function AITimeTravelPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">AI Model Time Travel</h1>
        <p className="text-gray-600">
          Analyze how AI models would have behaved in historical scenarios and track bias evolution over time.
        </p>
      </div>
      
      <AITimeTravel />
    </div>
  )
} 