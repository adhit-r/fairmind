import { AIEthicsObservatory } from "@/components/ai-ethics-observatory"

export default function AIEthicsObservatoryPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Global AI Ethics Observatory</h1>
        <p className="text-gray-600">
          Comprehensive monitoring and assessment of AI models against global ethics frameworks and regulations.
        </p>
      </div>
      
      <AIEthicsObservatory />
    </div>
  )
} 