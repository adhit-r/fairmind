"use client"

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/common/button';
import { Card } from '@/components/ui/common/card';
import { 
  Upload, 
  TestTube, 
  BarChart3, 
  CheckCircle,
  ArrowRight,
  ArrowLeft,
  Home,
  Users,
  Shield,
  Zap
} from 'lucide-react';

interface OnboardingStep {
  id: number;
  title: string;
  description: string;
  icon: React.ComponentType<any>;
  action?: () => void;
  actionText?: string;
  completed?: boolean;
}

interface OnboardingFlowProps {
  onComplete?: () => void;
  onSkip?: () => void;
}

export const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ 
  onComplete, 
  onSkip 
}) => {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  const steps: OnboardingStep[] = [
    {
      id: 1,
      title: "Welcome to FairMind",
      description: "Let's get you started with AI governance in just a few steps. We'll help you upload your first model and run some tests.",
      icon: Home,
      actionText: "Get Started"
    },
    {
      id: 2,
      title: "Upload Your First Model",
      description: "Start by uploading your ML model. We support various formats including .pkl, .joblib, .h5, and more.",
      icon: Upload,
      action: () => router.push('/model-upload'),
      actionText: "Upload Model"
    },
    {
      id: 3,
      title: "Run Bias Detection",
      description: "Test your model for fairness and bias issues. We'll analyze demographic parity, equalized odds, and more.",
      icon: TestTube,
      action: () => router.push('/model-testing'),
      actionText: "Run Tests"
    },
    {
      id: 4,
      title: "View Analytics",
      description: "Explore your model's performance, bias metrics, and compliance scores in our comprehensive dashboard.",
      icon: BarChart3,
      action: () => router.push('/analytics'),
      actionText: "View Analytics"
    },
    {
      id: 5,
      title: "Team Collaboration",
      description: "Invite your team members to collaborate on model governance and share insights.",
      icon: Users,
      actionText: "Invite Team"
    },
    {
      id: 6,
      title: "You're All Set!",
      description: "Congratulations! You've completed the onboarding. You can now start using FairMind for comprehensive AI governance.",
      icon: CheckCircle,
      actionText: "Go to Dashboard"
    }
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStepAction = () => {
    const step = steps[currentStep];
    if (step.action) {
      step.action();
    }
    
    // Mark step as completed
    if (!completedSteps.includes(step.id)) {
      setCompletedSteps([...completedSteps, step.id]);
    }
    
    // Move to next step
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      // Complete onboarding
      onComplete?.();
    }
  };

  const handleSkip = () => {
    onSkip?.();
  };

  const currentStepData = steps[currentStep];
  const progress = ((currentStep + 1) / steps.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl p-8">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
              Step {currentStep + 1} of {steps.length}
            </span>
            <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
              {Math.round(progress)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Step Content */}
        <div className="text-center mb-8">
          <div className="inline-flex p-4 rounded-full bg-blue-100 dark:bg-blue-900 mb-6">
            <currentStepData.icon className="w-8 h-8 text-blue-600 dark:text-blue-400" />
          </div>
          
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            {currentStepData.title}
          </h2>
          
          <p className="text-gray-600 dark:text-gray-300 text-lg leading-relaxed">
            {currentStepData.description}
          </p>
        </div>

        {/* Step Indicators */}
        <div className="flex justify-center mb-8">
          <div className="flex space-x-2">
            {steps.map((step, index) => (
              <div
                key={step.id}
                className={`w-3 h-3 rounded-full transition-all duration-300 ${
                  index === currentStep
                    ? 'bg-blue-600'
                    : completedSteps.includes(step.id)
                    ? 'bg-green-500'
                    : 'bg-gray-300 dark:bg-gray-600'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between items-center">
          <div className="flex space-x-3">
            {currentStep > 0 && (
              <Button
                variant="outline"
                onClick={handlePrevious}
                className="flex items-center"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Previous
              </Button>
            )}
            
            <Button
              variant="outline"
              onClick={handleSkip}
              className="text-gray-500 hover:text-gray-700"
            >
              Skip Onboarding
            </Button>
          </div>

          <div className="flex space-x-3">
            {currentStep < steps.length - 1 ? (
              <>
                <Button
                  onClick={handleStepAction}
                  className="bg-blue-600 hover:bg-blue-700 flex items-center"
                >
                  {currentStepData.actionText}
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
                <Button
                  variant="outline"
                  onClick={handleNext}
                >
                  Next
                </Button>
              </>
            ) : (
              <Button
                onClick={() => {
                  onComplete?.();
                  router.push('/dashboard');
                }}
                className="bg-green-600 hover:bg-green-700 flex items-center"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Complete & Go to Dashboard
              </Button>
            )}
          </div>
        </div>

        {/* Quick Tips */}
        {currentStep === 1 && (
          <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="flex items-start space-x-3">
              <Zap className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
              <div>
                <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-1">
                  Pro Tip
                </h4>
                <p className="text-sm text-blue-700 dark:text-blue-200">
                  You can always skip this onboarding and explore the platform directly. 
                  The dashboard has demo data to help you understand how FairMind works.
                </p>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
