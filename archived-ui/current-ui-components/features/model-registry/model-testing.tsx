"use client"

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/common/card';
import { Button } from '@/components/ui/common/button';
import { Badge } from '@/components/ui/common/badge';
import { 
  TestTube, 
  Shield, 
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3,
  Play
} from 'lucide-react';

export const ModelTesting: React.FC = () => {
  const [selectedModel, setSelectedModel] = useState('');
  const [selectedTests, setSelectedTests] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [testResults, setTestResults] = useState<any>(null);

  const availableModels = [
    { id: '1', name: 'Credit Risk Model v2.1', type: 'Classification' },
    { id: '2', name: 'Fraud Detection Model', type: 'Anomaly Detection' },
    { id: '3', name: 'Customer Churn Predictor', type: 'Classification' }
  ];

  const testTypes = [
    { id: 'bias', name: 'Bias Detection', description: 'Test for fairness and bias issues', icon: AlertTriangle },
    { id: 'security', name: 'Security Analysis', description: 'Check for vulnerabilities', icon: Shield },
    { id: 'performance', name: 'Performance Testing', description: 'Test model performance', icon: BarChart3 },
    { id: 'compliance', name: 'Compliance Check', description: 'Verify regulatory compliance', icon: CheckCircle }
  ];

  const handleRunTests = async () => {
    if (!selectedModel || selectedTests.length === 0) return;
    
    setIsRunning(true);
    // Simulate test execution
    setTimeout(() => {
      setTestResults({
        model: availableModels.find(m => m.id === selectedModel)?.name,
        tests: selectedTests,
        results: {
          bias: { score: 85, status: 'passed' },
          security: { score: 92, status: 'passed' },
          performance: { score: 78, status: 'warning' },
          compliance: { score: 88, status: 'passed' }
        }
      });
      setIsRunning(false);
    }, 3000);
  };

  const toggleTest = (testId: string) => {
    setSelectedTests(prev => 
      prev.includes(testId) 
        ? prev.filter(id => id !== testId)
        : [...prev, testId]
    );
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TestTube className="w-5 h-5" />
            Model Testing
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Model Selection */}
            <div>
              <label className="block text-sm font-medium mb-3">
                Select Model
              </label>
              <div className="grid gap-3">
                {availableModels.map((model) => (
                  <div
                    key={model.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedModel === model.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedModel(model.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-gray-900">
                          {model.name}
                        </div>
                        <div className="text-sm text-gray-600">
                          {model.type}
                        </div>
                      </div>
                      {selectedModel === model.id && (
                        <CheckCircle className="w-5 h-5 text-blue-600" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Test Selection */}
            <div>
              <label className="block text-sm font-medium mb-3">
                Select Tests
              </label>
              <div className="grid gap-3">
                {testTypes.map((test) => (
                  <div
                    key={test.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedTests.includes(test.id)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => toggleTest(test.id)}
                  >
                    <div className="flex items-center gap-3">
                      <test.icon className="w-5 h-5 text-gray-600" />
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">
                          {test.name}
                        </div>
                        <div className="text-sm text-gray-600">
                          {test.description}
                        </div>
                      </div>
                      {selectedTests.includes(test.id) && (
                        <CheckCircle className="w-5 h-5 text-blue-600" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <Button 
              onClick={handleRunTests}
              disabled={!selectedModel || selectedTests.length === 0 || isRunning}
              className="w-full"
            >
              {isRunning ? (
                <>
                  <Clock className="w-4 h-4 mr-2 animate-spin" />
                  Running Tests...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Run Selected Tests
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Test Results */}
      {testResults && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Test Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="text-sm text-gray-600">
                Model: <span className="font-medium">{testResults.model}</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(testResults.results).map(([testType, result]: [string, any]) => (
                  <div key={testType} className="text-center p-4 border rounded-lg">
                    <div className={`text-2xl font-bold ${
                      result.status === 'passed' ? 'text-green-600' :
                      result.status === 'warning' ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {result.score}%
                    </div>
                    <div className="text-sm text-gray-600 capitalize">
                      {testType}
                    </div>
                    <Badge className={`mt-2 ${
                      result.status === 'passed' ? 'bg-green-100 text-green-800' :
                      result.status === 'warning' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {result.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
