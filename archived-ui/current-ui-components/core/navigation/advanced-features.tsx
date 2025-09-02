"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  NeoContainer,
  NeoGrid,
  NeoHeading,
  NeoText,
  NeoAlert,
  NeoCard,
  NeoButton,
  NeoBadge,
  NeoProgress
} from "@/components/ui/common/neo-components"
import {
  Brain,
  Dna,
  Eye,
  TestTube,
  Globe,
  History,
  Layers,
  Search,
  Shield,
  Target,
  TrendingUp,
  Users,
  Zap
} from 'lucide-react'

interface AdvancedFeature {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  color: string
  category: 'discovery' | 'assessment' | 'security' | 'implementation' | 'excellence'
  journeyPhase: string
  path: string
  features: string[]
}

export function AdvancedFeatures() {
  const router = useRouter()
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  const advancedFeatures: AdvancedFeature[] = [
    {
      id: 'ai-dna-profiling',
      title: 'AI Model DNA Profiling',
      description: 'Track model lineage, analyze bias inheritance, and monitor AI model evolution',
      icon: <Dna className="h-6 w-6" />,
      color: 'bg-purple-500',
      category: 'discovery',
      journeyPhase: 'Discover',
      path: '/ai-dna-profiling',
      features: [
        'Model lineage tracking',
        'Bias inheritance analysis',
        'Performance evolution monitoring',
        'DNA signature generation',
        'Inheritance pattern detection'
      ]
    },
    {
      id: 'ai-ml-bom',
      title: 'AI/ML Bill of Materials',
      description: 'Comprehensive inventory of AI model components, dependencies, and supply chain',
      icon: <Layers className="h-6 w-6" />,
      color: 'bg-blue-500',
      category: 'discovery',
      journeyPhase: 'Discover',
      path: '/ai-ml-bom',
      features: [
        'Component inventory',
        'Dependency tracking',
        'Supply chain analysis',
        'Vulnerability assessment',
        'License compliance'
      ]
    },
    {
      id: 'aibom-dashboard',
      title: 'AIBOM Dashboard',
      description: 'Centralized dashboard for AI Bill of Materials management and monitoring',
      icon: <Brain className="h-6 w-6" />,
      color: 'bg-green-500',
      category: 'discovery',
      journeyPhase: 'Discover',
      path: '/aibom',
      features: [
        'Centralized management',
        'Real-time monitoring',
        'Risk assessment',
        'Compliance tracking',
        'Visual analytics'
      ]
    },
    {
      id: 'ai-ethics-observatory',
      title: 'AI Ethics Observatory',
      description: 'Global monitoring and assessment against ethics frameworks and regulations',
      icon: <Globe className="h-6 w-6" />,
      color: 'bg-orange-500',
      category: 'assessment',
      journeyPhase: 'Assess',
      path: '/ai-ethics-observatory',
      features: [
        'Global ethics frameworks',
        'Compliance assessment',
        'Regulatory monitoring',
        'Ethics scoring',
        'Recommendations engine'
      ]
    },
    {
      id: 'ai-circus',
      title: 'AI Circus Testing',
      description: 'Comprehensive testing environment for AI model robustness and edge cases',
      icon: <TestTube className="h-6 w-6" />,
      color: 'bg-red-500',
      category: 'assessment',
      journeyPhase: 'Assess',
      path: '/ai-circus',
      features: [
        'Robustness testing',
        'Edge case detection',
        'Adversarial testing',
        'Stress testing',
        'Performance validation'
      ]
    },
    {
      id: 'ai-genetic-engineering',
      title: 'AI Genetic Engineering',
      description: 'Advanced model optimization and genetic algorithm-based improvements',
      icon: <Zap className="h-6 w-6" />,
      color: 'bg-yellow-500',
      category: 'implementation',
      journeyPhase: 'Implement',
      path: '/ai-genetic-engineering',
      features: [
        'Model optimization',
        'Genetic algorithms',
        'Performance enhancement',
        'Bias reduction',
        'Automated improvement'
      ]
    },
    {
      id: 'ai-time-travel',
      title: 'AI Time Travel',
      description: 'Historical analysis and version control for AI model evolution',
      icon: <History className="h-6 w-6" />,
      color: 'bg-indigo-500',
      category: 'excellence',
      journeyPhase: 'Excel',
      path: '/ai-time-travel',
      features: [
        'Version control',
        'Historical analysis',
        'Rollback capabilities',
        'Evolution tracking',
        'Performance comparison'
      ]
    }
  ]

  const categories = [
    { id: 'all', name: 'All Features', icon: <Search className="h-4 w-4" /> },
    { id: 'discovery', name: 'Discovery', icon: <Search className="h-4 w-4" /> },
    { id: 'assessment', name: 'Assessment', icon: <Target className="h-4 w-4" /> },
    { id: 'security', name: 'Security', icon: <Shield className="h-4 w-4" /> },
    { id: 'implementation', name: 'Implementation', icon: <Layers className="h-4 w-4" /> },
    { id: 'excellence', name: 'Excellence', icon: <TrendingUp className="h-4 w-4" /> }
  ]

  const filteredFeatures = selectedCategory === 'all' 
    ? advancedFeatures 
    : advancedFeatures.filter(feature => feature.category === selectedCategory)

  const handleFeatureClick = (path: string) => {
    router.push(path)
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center mb-8">
        <NeoHeading size="xl" className="mb-4">
          <Brain className="h-8 w-8 inline mr-3" />
          Advanced AI Governance Features
        </NeoHeading>
        <NeoText className="text-xl max-w-3xl mx-auto">
          Specialized tools and features for comprehensive AI governance.
          Each feature integrates seamlessly with the journey phases.
        </NeoText>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 justify-center">
        {categories.map((category) => (
          <button
            key={category.id}
            onClick={() => setSelectedCategory(category.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg border-2 transition-all duration-200 ${
              selectedCategory === category.id
                ? 'border-black bg-gray-100'
                : 'border-gray-300 hover:border-black'
            }`}
          >
            {category.icon}
            <span className="neo-text neo-text--bold text-sm">{category.name}</span>
          </button>
        ))}
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredFeatures.map((feature) => (
          <div
            key={feature.id}
            className="neo-card cursor-pointer transition-all duration-300 hover:scale-105"
            onClick={() => handleFeatureClick(feature.path)}
          >
            <div className="flex items-start gap-4">
              <div className={`w-12 h-12 ${feature.color} rounded-lg flex items-center justify-center text-white`}>
                {feature.icon}
              </div>
              
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="neo-heading neo-heading--md">{feature.title}</h3>
                  <NeoBadge variant="info">{feature.journeyPhase}</NeoBadge>
                </div>
                
                <p className="neo-text text-gray-600 mb-3">{feature.description}</p>
                
                <div className="space-y-2">
                  <div className="text-sm text-gray-500">
                    <strong>Key Features:</strong>
                  </div>
                  <div className="space-y-1">
                    {feature.features.slice(0, 3).map((feat, index) => (
                      <div key={index} className="flex items-center gap-2 text-sm text-gray-600">
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full"></div>
                        {feat}
                      </div>
                    ))}
                    {feature.features.length > 3 && (
                      <div className="text-sm text-gray-500">
                        +{feature.features.length - 3} more features
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Journey Integration */}
      <NeoCard>
        <h2 className="neo-heading neo-heading--lg mb-6">Journey Integration</h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <Search className="h-8 w-8 mx-auto mb-2 text-blue-600" />
            <h3 className="neo-heading neo-heading--md mb-1">Discover</h3>
            <NeoText className="text-sm text-gray-600">DNA Profiling, BOM, Dashboard</NeoText>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <Target className="h-8 w-8 mx-auto mb-2 text-orange-600" />
            <h3 className="neo-heading neo-heading--md mb-1">Assess</h3>
            <NeoText className="text-sm text-gray-600">Ethics Observatory, Circus Testing</NeoText>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <Shield className="h-8 w-8 mx-auto mb-2 text-red-600" />
            <h3 className="neo-heading neo-heading--md mb-1">Secure</h3>
            <NeoText className="text-sm text-gray-600">Security Testing & Validation</NeoText>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <Layers className="h-8 w-8 mx-auto mb-2 text-green-600" />
            <h3 className="neo-heading neo-heading--md mb-1">Implement</h3>
            <NeoText className="text-sm text-gray-600">Genetic Engineering, Frameworks</NeoText>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <TrendingUp className="h-8 w-8 mx-auto mb-2 text-purple-600" />
            <h3 className="neo-heading neo-heading--md mb-1">Excel</h3>
            <NeoText className="text-sm text-gray-600">Time Travel, Continuous Improvement</NeoText>
          </div>
        </div>
      </NeoCard>

      {/* Usage Guidelines */}
      <NeoAlert variant="info">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <Eye className="h-6 w-6" />
          </div>
          <div>
            <NeoText variant="bold" className="mb-2">Advanced Features Guidelines</NeoText>
            <NeoText className="mb-2">• Use features in conjunction with the main journey phases for comprehensive governance</NeoText>
            <NeoText className="mb-2">• Each feature provides specialized capabilities that enhance the core journey process</NeoText>
            <NeoText>• Integrate advanced features based on your organization's specific AI governance needs</NeoText>
          </div>
        </div>
      </NeoAlert>
    </div>
  )
}

