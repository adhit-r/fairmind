"use client"

import React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/common/button';
import { Card } from '@/components/ui/common/card';
import { 
  Upload, 
  TestTube, 
  BarChart3, 
  Shield, 
  Users, 
  ArrowRight,
  Play,
  BookOpen,
  Zap
} from 'lucide-react';

export default function HomePage() {
  const router = useRouter();

  const quickActions = [
    {
      title: "Upload Your First Model",
      description: "Start by uploading your ML model for analysis",
      icon: Upload,
      action: () => router.push('/model-upload'),
      color: "bg-blue-500 hover:bg-blue-600",
      primary: true
    },
    {
      title: "View Dashboard",
      description: "See your models, tests, and analytics overview",
      icon: BarChart3,
      action: () => router.push('/dashboard'),
      color: "bg-green-500 hover:bg-green-600"
    },
    {
      title: "Run Model Tests",
      description: "Test your models for bias, security, and compliance",
      icon: TestTube,
      action: () => router.push('/model-testing'),
      color: "bg-purple-500 hover:bg-purple-600"
    }
  ];

  const features = [
    {
      title: "Model Management",
      description: "Upload, organize, and track all your ML models in one place",
      icon: Upload
    },
    {
      title: "Bias Detection",
      description: "Automatically detect and analyze bias in your models",
      icon: Shield
    },
    {
      title: "Security Analysis",
      description: "Identify vulnerabilities and security risks in your models",
      icon: Shield
    },
    {
      title: "Compliance Monitoring",
      description: "Ensure your models meet regulatory requirements",
      icon: Users
    },
    {
      title: "Team Collaboration",
      description: "Work together with your team on model governance",
      icon: Users
    },
    {
      title: "Real-time Analytics",
      description: "Get insights and reports on model performance",
      icon: BarChart3
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 dark:text-white mb-4">
            Welcome to <span className="text-blue-600 dark:text-blue-400">FairMind</span>
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            Your comprehensive AI governance platform for responsible machine learning
          </p>
        </div>

        {/* Quick Start Section */}
        <div className="mb-16">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Get Started in 3 Simple Steps
            </h2>
            <p className="text-gray-600 dark:text-gray-300">
              Choose how you'd like to begin your AI governance journey
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {quickActions.map((action, index) => (
              <Card key={index} className="p-6 hover:shadow-lg transition-shadow cursor-pointer" onClick={action.action}>
                <div className="text-center">
                  <div className={`inline-flex p-3 rounded-full ${action.color} text-white mb-4`}>
                    <action.icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    {action.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-300 mb-4">
                    {action.description}
                  </p>
                  <Button 
                    className={action.primary ? "w-full" : "w-full bg-gray-100 hover:bg-gray-200 text-gray-900"}
                    onClick={(e) => {
                      e.stopPropagation();
                      action.action();
                    }}
                  >
                    {action.primary ? (
                      <>
                        <Play className="w-4 h-4 mr-2" />
                        Get Started
                      </>
                    ) : (
                      <>
                        <ArrowRight className="w-4 h-4 mr-2" />
                        Explore
                      </>
                    )}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Features Overview */}
        <div className="mb-16">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Everything You Need for AI Governance
            </h2>
            <p className="text-gray-600 dark:text-gray-300">
              Comprehensive tools to ensure your AI models are fair, secure, and compliant
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {features.map((feature, index) => (
              <Card key={index} className="p-6">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                      <feature.icon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-300">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Demo Section */}
        <div className="text-center">
          <Card className="p-8 max-w-4xl mx-auto bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700">
            <div className="mb-6">
              <Zap className="w-12 h-12 text-blue-600 dark:text-blue-400 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                New to FairMind?
              </h2>
              <p className="text-gray-600 dark:text-gray-300">
                Take our guided tour to learn how to use the platform effectively
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                onClick={() => router.push('/onboarding')}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <BookOpen className="w-4 h-4 mr-2" />
                Start Guided Tour
              </Button>
              <Button 
                variant="outline"
                onClick={() => router.push('/dashboard')}
              >
                <BarChart3 className="w-4 h-4 mr-2" />
                Skip to Dashboard
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
