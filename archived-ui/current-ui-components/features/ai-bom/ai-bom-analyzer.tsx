"use client"

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/common/card';
import { Button } from '@/components/ui/common/button';
import { Input } from '@/components/ui/common/input';
import { Textarea } from '@/components/ui/common/textarea';
import { 
  Upload, 
  Search, 
  FileText, 
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3
} from 'lucide-react';

export const AIBOMAnalyzer: React.FC = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<any>(null);

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    // Simulate analysis
    setTimeout(() => {
      setAnalysisResults({
        components: 15,
        vulnerabilities: 2,
        licenses: 8,
        riskScore: 75,
        complianceScore: 82
      });
      setIsAnalyzing(false);
    }, 2000);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            AI BOM Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                BOM Document
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p className="text-gray-600">Upload your AI BOM document</p>
                <Button className="mt-2" variant="outline">
                  Choose File
                </Button>
              </div>
            </div>
            
            <Button 
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="w-full"
            >
              {isAnalyzing ? (
                <>
                  <Clock className="w-4 h-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2" />
                  Analyze BOM
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {analysisResults && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Analysis Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {analysisResults.components}
                </div>
                <div className="text-sm text-gray-600">Components</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {analysisResults.vulnerabilities}
                </div>
                <div className="text-sm text-gray-600">Vulnerabilities</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {analysisResults.licenses}
                </div>
                <div className="text-sm text-gray-600">Licenses</div>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {analysisResults.riskScore}%
                </div>
                <div className="text-sm text-gray-600">Risk Score</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
