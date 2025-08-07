import { AICircus } from "@/components/ai-circus"

export default function AICircusPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">AI Model Circus</h1>
        <p className="text-gray-600">
          Comprehensive testing arena for AI models - stress tests, edge cases, adversarial challenges, and more.
        </p>
      </div>
      
      <AICircus />
    </div>
  )
} 