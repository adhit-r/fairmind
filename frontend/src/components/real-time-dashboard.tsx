"use client"

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  Shield, 
  Brain, 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown, 
  Wifi, 
  WifiOff,
  RefreshCw,
  Clock
} from "lucide-react";
import { 
  useDashboardData, 
  useComplianceStatus, 
  useGovernanceMetrics,
  useActiveModels,
  useRecentSimulations,
  supabaseRealTimeService 
} from '@/lib/supabase-realtime';
import { AIGovernanceChart } from "./charts/ai-governance-chart";
import { DistributionChart } from "./charts/distribution-chart";
import { PerformanceMatrix } from "./charts/performance-matrix";
import { NISTComplianceMatrix } from "./charts/nist-compliance-matrix";
import { BiasDetectionRadar } from "./charts/bias-detection-radar";
import { LLMSafetyDashboard } from "./charts/llm-safety-dashboard";

export function RealTimeDashboard() {
  const { data: dashboardData, isLoading: dashboardLoading, error: dashboardError } = useDashboardData();
  const { data: complianceStatus, isLoading: complianceLoading } = useComplianceStatus();
  const { data: governanceMetrics, isLoading: metricsLoading } = useGovernanceMetrics();
  const { data: activeModels, isLoading: modelsLoading } = useActiveModels();
  const { data: recentSimulations, isLoading: simulationsLoading } = useRecentSimulations();

  const [connectionStatus, setConnectionStatus] = React.useState(supabaseRealTimeService.getConnectionStatus());

  // Update connection status periodically
  React.useEffect(() => {
    const interval = setInterval(() => {
      setConnectionStatus(supabaseRealTimeService.getConnectionStatus());
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleRefresh = async () => {
    try {
      await supabaseRealTimeService.refreshData();
    } catch (error) {
      console.error('Manual refresh failed:', error);
    }
  };

  const isLoading = dashboardLoading || complianceLoading || metricsLoading || modelsLoading || simulationsLoading;

  if (dashboardError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <h1 className="text-2xl font-bold tracking-tight">AI_GOVERNANCE_DASHBOARD</h1>
            <p className="text-sm text-muted-foreground font-mono">
              COMPREHENSIVE.AI.RISK.MANAGEMENT.AND.COMPLIANCE.MONITORING.PLATFORM
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="destructive" className="flex items-center gap-1">
              <WifiOff className="h-3 w-3" />
              DISCONNECTED
            </Badge>
            <Button onClick={handleRefresh} size="sm" variant="outline">
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <Card>
          <CardContent className="p-8">
            <div className="text-center space-y-4">
              <AlertTriangle className="h-12 w-12 text-destructive mx-auto" />
              <h3 className="text-lg font-semibold">Connection Error</h3>
              <p className="text-muted-foreground">
                Unable to connect to the backend service. Please check your connection and try again.
              </p>
              <Button onClick={handleRefresh}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry Connection
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with connection status */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-2xl font-bold tracking-tight">AI_GOVERNANCE_DASHBOARD</h1>
          <p className="text-sm text-muted-foreground font-mono">
            COMPREHENSIVE.AI.RISK.MANAGEMENT.AND.COMPLIANCE.MONITORING.PLATFORM
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge 
            variant={connectionStatus.isConnected ? "default" : "destructive"} 
            className="flex items-center gap-1"
          >
            {connectionStatus.isConnected ? (
              <>
                <Wifi className="h-3 w-3" />
                {connectionStatus.type.toUpperCase()}
              </>
            ) : (
              <>
                <WifiOff className="h-3 w-3" />
                DISCONNECTED
              </>
            )}
          </Badge>
          {dashboardData?.lastUpdated && (
            <Badge variant="outline" className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {new Date(dashboardData.lastUpdated).toLocaleTimeString()}
            </Badge>
          )}
          <Button onClick={handleRefresh} size="sm" variant="outline" disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="grid gap-4 md:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardContent className="p-4">
                <div className="animate-pulse">
                  <div className="h-4 bg-muted rounded w-1/2 mb-2"></div>
                  <div className="h-6 bg-muted rounded w-1/3"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Real-time metrics cards */}
      {!isLoading && complianceStatus && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">NIST_COMPLIANCE</p>
                  <p className="text-lg font-bold">{complianceStatus.nistCompliance}%</p>
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  <div className="flex items-center gap-1">
                    <TrendingUp className="h-3 w-3" />
                    <span className="text-xs">+3.2%</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">ACTIVE_MODELS</p>
                  <p className="text-lg font-bold">{complianceStatus.activeModels}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Brain className="h-4 w-4" />
                  <div className="flex items-center gap-1">
                    <TrendingUp className="h-3 w-3" />
                    <span className="text-xs">+12</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">CRITICAL_RISKS</p>
                  <p className="text-lg font-bold">{complianceStatus.criticalRisks}</p>
                </div>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  <div className="flex items-center gap-1">
                    <TrendingDown className="h-3 w-3" />
                    <span className="text-xs">-2</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">LLM_SAFETY_SCORE</p>
                  <p className="text-lg font-bold">{complianceStatus.llmSafetyScore}%</p>
                </div>
                <div className="flex items-center gap-2">
                  <Brain className="h-4 w-4" />
                  <div className="flex items-center gap-1">
                    <TrendingUp className="h-3 w-3" />
                    <span className="text-xs">+5.1%</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Charts section */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>AI_GOVERNANCE_METRICS</CardTitle>
            <CardDescription>Real-time governance performance tracking</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <AIGovernanceChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>BIAS_DETECTION_RADAR</CardTitle>
            <CardDescription>Multi-dimensional bias analysis</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <BiasDetectionRadar />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>LLM_SAFETY_DASHBOARD</CardTitle>
            <CardDescription>Large language model safety monitoring</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <LLMSafetyDashboard />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>DISTRIBUTION_ANALYSIS</CardTitle>
            <CardDescription>Data distribution and fairness metrics</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <DistributionChart />
          </CardContent>
        </Card>
      </div>

      {/* Advanced analytics */}
      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>PERFORMANCE_MATRIX</CardTitle>
            <CardDescription>Model performance and accuracy analysis</CardDescription>
          </CardHeader>
          <CardContent>
            <PerformanceMatrix />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>NIST_COMPLIANCE_MATRIX</CardTitle>
            <CardDescription>Regulatory compliance assessment</CardDescription>
          </CardHeader>
          <CardContent>
            <NISTComplianceMatrix />
          </CardContent>
        </Card>
      </div>

      {/* Recent activity */}
      {recentSimulations && recentSimulations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>RECENT_SIMULATIONS</CardTitle>
            <CardDescription>Latest simulation activities and results</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentSimulations.slice(0, 5).map((simulation) => (
                <div key={simulation.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium">{simulation.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {simulation.type} • {simulation.status}
                    </p>
                  </div>
                  <Badge variant={simulation.status === 'COMPLETED' ? 'default' : 'secondary'}>
                    {simulation.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 