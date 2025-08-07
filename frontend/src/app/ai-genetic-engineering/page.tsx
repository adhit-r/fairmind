import { AIGeneticEngineering } from "@/components/ai-genetic-engineering"

export default function AIGeneticEngineeringPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">AI Model Genetic Engineering</h1>
        <p className="text-gray-600">
          Safely modify AI models to remove bias, improve fairness, and enhance ethical alignment through advanced genetic engineering techniques.
        </p>
      </div>
      
      <AIGeneticEngineering />
    </div>
  )
} 