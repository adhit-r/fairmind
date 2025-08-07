import { AIDNAProfiler } from "@/components/ai-dna-profiler"

export default function AIDNAProfilingPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">AI Model DNA Profiling</h1>
        <p className="text-gray-600">
          Track model lineage, analyze bias inheritance, and monitor AI model evolution through comprehensive DNA profiling.
        </p>
      </div>
      
      <AIDNAProfiler />
    </div>
  )
} 