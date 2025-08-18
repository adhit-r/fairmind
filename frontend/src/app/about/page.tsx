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
  Play
} from "lucide-react"
import Link from "next/link"

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <Badge className="mb-4 bg-blue-100 text-blue-800">
            <Shield className="h-4 w-4 mr-2" />
            About Fairmind
          </Badge>
          
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            What is <span className="text-blue-600">Fairmind</span>?
          </h1>
          
          <p className="text-xl text-gray-600 mb-8">
            Fairmind is an AI governance platform that helps organizations build responsible, 
            fair, and trustworthy artificial intelligence systems.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/bias-test">
              <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
                <Play className="h-5 w-5 mr-2" />
                Try It Now
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline">
                <ArrowRight className="h-5 w-5 mr-2" />
                Explore Features
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* What We Do */}
      <section className="py-16 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              What Does Fairmind Do?
            </h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              We solve the biggest problem in AI today: bias and unfairness. 
              Our platform makes it easy to detect, understand, and fix bias in AI systems.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card className="text-center">
              <CardHeader>
                <div className="flex justify-center mb-4">
                  <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                    <AlertTriangle className="h-8 w-8 text-red-600" />
                  </div>
                </div>
                <CardTitle>Detect Bias</CardTitle>
                <CardDescription>
                  Automatically find 8 types of bias in your AI models
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    Reporting bias
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    Historical bias
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    Selection bias
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    And 5 more types
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardHeader>
                <div className="flex justify-center mb-4">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                    <Target className="h-8 w-8 text-green-600" />
                  </div>
                </div>
                <CardTitle>Ensure Fairness</CardTitle>
                <CardDescription>
                  Test your models for fairness across different groups
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    Demographic parity
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    Equality of opportunity
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    Statistical parity
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    Counterfactual fairness
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardHeader>
                <div className="flex justify-center mb-4">
                  <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center">
                    <Award className="h-8 w-8 text-purple-600" />
                  </div>
                </div>
                <CardTitle>Build Trust</CardTitle>
                <CardDescription>
                  Demonstrate responsible AI practices to stakeholders
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    Compliance documentation
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    Audit-ready reports
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    Professional recognition
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    Team achievements
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Why It Matters */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Why Does This Matter?
            </h2>
            <p className="text-lg text-gray-600">
              AI bias is not just a technical problem—it's a business and social problem
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <Card className="border-red-200 bg-red-50">
              <CardHeader>
                <CardTitle className="text-red-800 flex items-center">
                  <AlertTriangle className="h-6 w-6 mr-2" />
                  The Problem
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-red-800">AI Bias is Everywhere</h4>
                    <p className="text-red-700 text-sm">78% of AI systems show bias against protected groups</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-red-800">Costly Lawsuits</h4>
                    <p className="text-red-700 text-sm">AI bias lawsuits cost companies $100M+ annually</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-red-800">Regulatory Pressure</h4>
                    <p className="text-red-700 text-sm">New laws require bias testing and documentation</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-red-800">Reputation Risk</h4>
                    <p className="text-red-700 text-sm">Public AI failures destroy brand trust overnight</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-green-200 bg-green-50">
              <CardHeader>
                <CardTitle className="text-green-800 flex items-center">
                  <CheckCircle className="h-6 w-6 mr-2" />
                  Our Solution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-green-800">Proactive Detection</h4>
                    <p className="text-green-700 text-sm">Find bias before it reaches your users</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-green-800">Compliance Ready</h4>
                    <p className="text-green-700 text-sm">Generate audit-ready documentation automatically</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-green-800">Risk Mitigation</h4>
                    <p className="text-green-700 text-sm">Prevent costly lawsuits and reputation damage</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-green-800">Competitive Advantage</h4>
                    <p className="text-green-700 text-sm">Build trust and demonstrate responsible AI practices</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Our Mission */}
      <section className="py-16 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-6">
            Our Mission
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            To make AI governance accessible, comprehensive, and engaging for every organization 
            that wants to build responsible AI systems.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Brain className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Accessible</h3>
              <p className="text-gray-600">
                Simple interface that anyone can use, not just AI experts
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Comprehensive</h3>
              <p className="text-gray-600">
                Cover all types of bias and fairness metrics
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Star className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Engaging</h3>
              <p className="text-gray-600">
                Gamified experience that motivates teams to participate
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              How Does Fairmind Work?
            </h2>
            <p className="text-lg text-gray-600">
              Simple 3-step process to build responsible AI
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-blue-600">1</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Upload & Configure</h3>
              <p className="text-gray-600">
                Upload your AI model or dataset. Select sensitive attributes 
                (like gender, race, age) and target variables to analyze.
              </p>
            </div>

            <div className="text-center">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-green-600">2</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Run Analysis</h3>
              <p className="text-gray-600">
                Our AI automatically analyzes your model for 8 types of bias 
                and calculates fairness metrics across different groups.
              </p>
            </div>

            <div className="text-center">
              <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-purple-600">3</span>
              </div>
              <h3 className="text-xl font-semibold mb-3">Get Insights & Fix</h3>
              <p className="text-gray-600">
                Receive detailed reports with specific recommendations 
                to fix bias issues and improve fairness.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-blue-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join organizations building responsible AI with Fairmind
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/bias-test">
              <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100">
                <Play className="h-5 w-5 mr-2" />
                Try Free Demo
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-blue-600">
                <ArrowRight className="h-5 w-5 mr-2" />
                Explore Platform
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
