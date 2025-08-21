"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell
} from 'recharts';

interface FairnessMetrics {
  statistical_parity_difference: number;
  equalized_odds_tpr_difference: number;
  equalized_odds_fpr_difference: number;
  equal_opportunity_difference: number;
  group_metrics: Record<string, any>;
}

interface BiasDetection {
  high_bias_attributes: string[];
  bias_severity: Record<string, string>;
  bias_direction: Record<string, string>;
}

interface FairnessAnalysisResult {
  timestamp: string;
  analysis_config: Record<string, any>;
  fairness_metrics: Record<string, FairnessMetrics>;
  bias_detection: BiasDetection;
  recommendations: string[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export default function AdvancedFairnessDashboard() {
  const [analysisResult, setAnalysisResult] = useState<FairnessAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sampleData, setSampleData] = useState({
    predictions: [0.8, 0.6, 0.9, 0.3, 0.7, 0.4, 0.8, 0.5, 0.9, 0.2],
    labels: [1, 1, 1, 0, 1, 0, 1, 0, 1, 0],
    sensitive_attr: [1, 1, 0, 0, 1, 0, 1, 0, 0, 1]
  });

  const runSampleAnalysis = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/advanced-fairness/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_predictions: sampleData.predictions,
          ground_truth: sampleData.labels,
          sensitive_attributes: {
            gender: sampleData.sensitive_attr
          },
          analysis_config: {
            threshold: 0.5,
            metrics: ['statistical_parity', 'equalized_odds', 'equal_opportunity'],
            bias_threshold: 0.1,
            include_recommendations: true
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setAnalysisResult(result.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getBiasSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const prepareChartData = (groupMetrics: Record<string, any>) => {
    return Object.entries(groupMetrics).map(([group, metrics]) => ({
      group,
      tpr: metrics.true_positive_rate || 0,
      fpr: metrics.false_positive_rate || 0,
      accuracy: metrics.accuracy || 0
    }));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Advanced Fairness Analysis</h1>
          <p className="text-muted-foreground">
            Comprehensive bias detection and fairness evaluation using TensorFlow Fairness Indicators
          </p>
        </div>
        <Button onClick={runSampleAnalysis} disabled={loading}>
          {loading ? 'Analyzing...' : 'Run Sample Analysis'}
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {analysisResult && (
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="metrics">Fairness Metrics</TabsTrigger>
            <TabsTrigger value="bias">Bias Detection</TabsTrigger>
            <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {Object.entries(analysisResult.fairness_metrics).map(([attr, metrics]) => (
                <Card key={attr}>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      {attr.charAt(0).toUpperCase() + attr.slice(1)}
                    </CardTitle>
                    <Badge variant={metrics.statistical_parity_difference > 0.1 ? "destructive" : "secondary"}>
                      {metrics.statistical_parity_difference > 0.1 ? "High Bias" : "Low Bias"}
                    </Badge>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {(metrics.statistical_parity_difference * 100).toFixed(1)}%
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Statistical Parity Difference
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Fairness Metrics Summary</CardTitle>
                <CardDescription>
                  Key fairness indicators across all sensitive attributes
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(analysisResult.fairness_metrics).map(([attr, metrics]) => (
                    <div key={attr} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="font-medium">{attr}</Label>
                        <div className="flex space-x-4 text-sm">
                          <span>SP: {(metrics.statistical_parity_difference * 100).toFixed(1)}%</span>
                          <span>EO: {(metrics.equal_opportunity_difference * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                      <Progress 
                        value={Math.min(metrics.statistical_parity_difference * 1000, 100)} 
                        className="h-2"
                      />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="metrics" className="space-y-4">
            {Object.entries(analysisResult.fairness_metrics).map(([attr, metrics]) => (
              <Card key={attr}>
                <CardHeader>
                  <CardTitle>{attr.charAt(0).toUpperCase() + attr.slice(1)} Fairness Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-4">
                      <div>
                        <Label>Statistical Parity Difference</Label>
                        <div className="text-2xl font-bold">
                          {(metrics.statistical_parity_difference * 100).toFixed(2)}%
                        </div>
                      </div>
                      <div>
                        <Label>Equal Opportunity Difference</Label>
                        <div className="text-2xl font-bold">
                          {(metrics.equal_opportunity_difference * 100).toFixed(2)}%
                        </div>
                      </div>
                      <div>
                        <Label>Equalized Odds TPR Difference</Label>
                        <div className="text-2xl font-bold">
                          {(metrics.equalized_odds_tpr_difference * 100).toFixed(2)}%
                        </div>
                      </div>
                    </div>
                    
                    {metrics.group_metrics && (
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={prepareChartData(metrics.group_metrics)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="group" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="tpr" fill="#0088FE" name="True Positive Rate" />
                          <Bar dataKey="fpr" fill="#00C49F" name="False Positive Rate" />
                        </BarChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="bias" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Bias Detection Results</CardTitle>
                <CardDescription>
                  Automated bias pattern detection and severity assessment
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label className="text-base font-medium">High Bias Attributes</Label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {analysisResult.bias_detection.high_bias_attributes.length > 0 ? (
                        analysisResult.bias_detection.high_bias_attributes.map((attr) => (
                          <Badge key={attr} variant="destructive">
                            {attr}
                          </Badge>
                        ))
                      ) : (
                        <Badge variant="secondary">None detected</Badge>
                      )}
                    </div>
                  </div>

                  <div>
                    <Label className="text-base font-medium">Bias Severity by Attribute</Label>
                    <div className="grid gap-2 mt-2">
                      {Object.entries(analysisResult.bias_detection.bias_severity).map(([attr, severity]) => (
                        <div key={attr} className="flex items-center justify-between p-2 border rounded">
                          <span className="font-medium">{attr}</span>
                          <Badge className={getBiasSeverityColor(severity)}>
                            {severity}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="recommendations" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Automated Recommendations</CardTitle>
                <CardDescription>
                  AI-generated suggestions for bias mitigation and fairness improvement
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analysisResult.recommendations.map((recommendation, index) => (
                    <div key={index} className="flex items-start space-x-3 p-3 border rounded-lg">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                      <p className="text-sm">{recommendation}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {!analysisResult && !loading && (
        <Card>
          <CardHeader>
            <CardTitle>Get Started</CardTitle>
            <CardDescription>
              Run a sample fairness analysis to see the advanced capabilities in action
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <Label>Sample Predictions</Label>
                  <Textarea 
                    value={JSON.stringify(sampleData.predictions, null, 2)}
                    readOnly
                    className="h-20"
                  />
                </div>
                <div>
                  <Label>Sample Labels</Label>
                  <Textarea 
                    value={JSON.stringify(sampleData.labels, null, 2)}
                    readOnly
                    className="h-20"
                  />
                </div>
                <div>
                  <Label>Sample Sensitive Attribute</Label>
                  <Textarea 
                    value={JSON.stringify(sampleData.sensitive_attr, null, 2)}
                    readOnly
                    className="h-20"
                  />
                </div>
              </div>
              <Button onClick={runSampleAnalysis} className="w-full">
                Run Sample Analysis
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
