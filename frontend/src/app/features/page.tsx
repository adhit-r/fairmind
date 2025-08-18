"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Badge } from "@/components/ui/common/badge"
import { Button } from "@/components/ui/common/button"
import { 
  Shield, 
  Target, 
  Users, 
  CheckCircle, 
  AlertTriangle,
  Brain,
  Zap,
  Award,
  Star,
  ArrowRight,
  Play,
  BarChart3,
  FileText,
  TrendingUp,
  Eye,
  Settings,
  PieChart,
  Globe,
  Lock,
  Database,
  Search,
  Filter
} from "lucide-react"
import Link from "next/link"

export default function FeaturesPage() {
  const features = [
    {
      icon: <Shield className="h-8 w-8 text-blue-600" />,
      title: "Bias Detection",
      description: "Automatically detect 8 types of bias in your AI models",
      details: [
        "Reporting bias - when dataset doesn't reflect real-world frequency",
        "Historical bias - when data reflects past inequities", 
        "Selection bias - when sampling isn't representative",
        "Group attribution bias - when generalizing to entire groups",
        "Implicit bias - when assumptions affect decisions",
        "Confirmation bias - when processing affirms beliefs",
        "Experimenter bias - when training aligns with hypotheses",
        "Automation bias - when favoring automated over manual results"
      ],
      benefits: ["Prevent discrimination", "Meet compliance requirements", "Build fair AI systems"],
      link: "/bias-detection"
    },
    {
      icon: <Target className="h-8 w-8 text-green-600" />,
      title: "Fairness Testing",
      description: "Test your models for fairness across different demographic groups",
      details: [
        "Demographic parity - equal acceptance rates across groups",
        "Equality of opportunity - equal true positive rates",
        "Statistical parity - fair distribution of outcomes",
        "Counterfactual fairness - fair treatment in hypothetical scenarios"
      ],
      benefits: ["Ensure equal treatment", "Meet legal requirements", "Build inclusive AI"],
      link: "/bias-test"
    },
    {
      icon: <Globe className="h-8 w-8 text-purple-600" />,
      title: "Geographic Bias Detection",
      description: "Detect and analyze bias based on geographic location",
      details: [
        "Regional performance analysis",
        "Geographic data distribution",
        "Location-based fairness metrics",
        "Cultural bias identification"
      ],
      benefits: ["Global fairness", "Cultural sensitivity", "Regional compliance"],
      link: "/geographic-bias"
    },
    {
      icon: <BarChart3 className="h-8 w-8 text-orange-600" />,
      title: "Comprehensive Analytics",
      description: "Detailed analytics and reporting for AI governance",
      details: [
        "Performance metrics by group",
        "Bias trend analysis over time",
        "Risk assessment scoring",
        "Compliance reporting"
      ],
      benefits: ["Data-driven decisions", "Track improvements", "Demonstrate compliance"],
      link: "/analytics"
    },
    {
      icon: <Award className="h-8 w-8 text-yellow-600" />,
      title: "Governance Center",
      description: "Gamified AI governance with achievements and team collaboration",
      details: [
        "Governance score tracking",
        "Achievement system (Bronze to Platinum)",
        "Team challenges and objectives",
        "Professional leaderboards"
      ],
      benefits: ["Engage your team", "Build culture", "Professional recognition"],
      link: "/governance-center"
    },
    {
      icon: <Database className="h-8 w-8 text-indigo-600" />,
      title: "Model Registry",
      description: "Centralized management of AI models and their governance data",
      details: [
        "Model versioning and tracking",
        "Bias analysis history",
        "Performance benchmarks",
        "Compliance documentation"
      ],
      benefits: ["Organized workflow", "Audit trail", "Team collaboration"],
      link: "/models"
    },
    {
      icon: <Lock className="h-8 w-8 text-red-600" />,
      title: "Security Testing",
      description: "OWASP Top 10 AI/LLM security testing and analysis",
      details: [
        "Prompt injection testing",
        "Output validation",
        "Training data poisoning detection",
        "Supply chain vulnerability scanning"
      ],
      benefits: ["Secure AI systems", "Prevent attacks", "Meet security standards"],
      link: "/owasp-security"
    },
    {
      icon: <FileText className="h-8 w-8 text-teal-600" />,
      title: "AI Bill of Materials",
      description: "Comprehensive tracking of AI model components and dependencies",
      details: [
        "Component inventory",
        "Vulnerability scanning",
        "License compliance",
        "Risk assessment"
      ],
      benefits: ["Transparency", "Compliance", "Risk management"],
      link: "/ai-ml-bom"
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <Badge className="mb-4 bg-blue-100 text-blue-800">
            <Star className="h-4 w-4 mr-2" />
            Features
          </Badge>
          
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Complete AI Governance <span className="text-blue-600">Platform</span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Everything you need to build responsible, fair, and trustworthy AI systems. 
            From bias detection to compliance tracking, we've got you covered.
          </p>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        {feature.icon}
                      </div>
                      <div>
                        <CardTitle className="text-xl">{feature.title}</CardTitle>
                        <CardDescription className="text-base">
                          {feature.description}
                        </CardDescription>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">What it does:</h4>
                    <ul className="space-y-1 text-sm text-gray-600">
                      {feature.details.map((detail, idx) => (
                        <li key={idx} className="flex items-start">
                          <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 mr-2 flex-shrink-0"></div>
                          {detail}
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Benefits:</h4>
                    <div className="flex flex-wrap gap-2">
                      {feature.benefits.map((benefit, idx) => (
                        <Badge key={idx} variant="secondary" className="text-xs">
                          {benefit}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  
                  <div className="pt-4">
                    <Link href={feature.link}>
                      <Button variant="outline" size="sm" className="w-full">
                        <Eye className="h-4 w-4 mr-2" />
                        Explore {feature.title}
                        <ArrowRight className="h-4 w-4 ml-2" />
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How Features Work Together */}
      <section className="py-16 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              How Features Work Together
            </h2>
            <p className="text-lg text-gray-600">
              Fairmind's features are designed to work seamlessly together for complete AI governance
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-blue-600">1</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Detect Issues</h3>
              <p className="text-gray-600">
                Use bias detection, fairness testing, and security analysis to identify problems
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-green-600">2</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Track Progress</h3>
              <p className="text-gray-600">
                Monitor improvements with analytics and governance scoring
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-purple-600">3</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Demonstrate Compliance</h3>
              <p className="text-gray-600">
                Generate reports and documentation for stakeholders and regulators
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-blue-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Choose a feature to explore or start with our bias detection demo
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/bias-test">
              <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100">
                <Play className="h-5 w-5 mr-2" />
                Try Bias Detection
              </Button>
            </Link>
            <Link href="/about">
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-blue-600">
                <ArrowRight className="h-5 w-5 mr-2" />
                Learn More
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
