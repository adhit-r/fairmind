"use client";

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Treemap,
  TreemapItem,
} from 'recharts';
import { 
  AlertTriangle, 
  Shield, 
  Package, 
  Database, 
  Code, 
  FileText,
  Download,
  Eye,
  Search,
  Filter
} from 'lucide-react';

interface CycloneDXComponent {
  type: string;
  name: string;
  version: string;
  description?: string;
  licenses?: Array<{ license: { id: string } }>;
  externalReferences?: Array<{ type: string; url: string }>;
  properties?: Array<{ name: string; value: string }>;
  vulnerabilities?: Array<any>;
  bomRef: string;
  purl?: string;
  cpe?: string;
}

interface Vulnerability {
  id: string;
  source: {
    name: string;
    url: string;
  };
  ratings: Array<{
    source: { name: string };
    score?: number;
    severity?: string;
  }>;
  description: string;
  affects: Array<{ ref: string }>;
}

interface CycloneDXBOM {
  bomFormat: string;
  specVersion: string;
  version: number;
  metadata: {
    timestamp: string;
    tools: Array<{ vendor: string; name: string; version: string }>;
    component: {
      name: string;
      version: string;
      description: string;
    };
  };
  components: CycloneDXComponent[];
  dependencies?: Array<{ ref: string; dependsOn: string[] }>;
  vulnerabilities?: Vulnerability[];
}

interface BOMVisualizerProps {
  bomData: CycloneDXBOM;
  organizationId: string;
}

const COLORS = {
  library: '#3b82f6',
  model: '#10b981',
  dataset: '#f59e0b',
  application: '#8b5cf6',
  framework: '#ef4444',
  tool: '#06b6d4',
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#d97706',
  low: '#059669',
  unknown: '#6b7280'
};

export default function CycloneDXBOMVisualizer({ bomData, organizationId }: BOMVisualizerProps) {
  const [filteredComponents, setFilteredComponents] = useState<CycloneDXComponent[]>(bomData.components);
  const [filteredVulnerabilities, setFilteredVulnerabilities] = useState<Vulnerability[]>(bomData.vulnerabilities || []);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');

  // Process data for visualizations
  const componentTypeData = React.useMemo(() => {
    const typeCount = bomData.components.reduce((acc, comp) => {
      acc[comp.type] = (acc[comp.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(typeCount).map(([type, count]) => ({
      name: type,
      value: count,
      color: COLORS[type as keyof typeof COLORS] || COLORS.unknown
    }));
  }, [bomData.components]);

  const vulnerabilitySeverityData = React.useMemo(() => {
    if (!bomData.vulnerabilities) return [];
    
    const severityCount = bomData.vulnerabilities.reduce((acc, vuln) => {
      const severity = vuln.ratings?.[0]?.severity || 'unknown';
      acc[severity] = (acc[severity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(severityCount).map(([severity, count]) => ({
      name: severity.toUpperCase(),
      value: count,
      color: COLORS[severity.toLowerCase() as keyof typeof COLORS] || COLORS.unknown
    }));
  }, [bomData.vulnerabilities]);

  const frameworkData = React.useMemo(() => {
    const frameworkCount = bomData.components
      .filter(comp => comp.type === 'model')
      .reduce((acc, comp) => {
        const framework = comp.properties?.find(p => p.name === 'framework')?.value || 'unknown';
        acc[framework] = (acc[framework] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

    return Object.entries(frameworkCount).map(([framework, count]) => ({
      name: framework,
      value: count
    }));
  }, [bomData.components]);

  // Risk assessment
  const riskAssessment = React.useMemo(() => {
    const totalComponents = bomData.components.length;
    const totalVulnerabilities = bomData.vulnerabilities?.length || 0;
    const criticalVulns = bomData.vulnerabilities?.filter(v => 
      v.ratings?.[0]?.severity === 'CRITICAL'
    ).length || 0;
    const highVulns = bomData.vulnerabilities?.filter(v => 
      v.ratings?.[0]?.severity === 'HIGH'
    ).length || 0;

    return {
      totalComponents,
      totalVulnerabilities,
      criticalVulns,
      highVulns,
      riskScore: totalVulnerabilities > 0 ? Math.min(100, (criticalVulns * 10 + highVulns * 5) / totalComponents * 100) : 0
    };
  }, [bomData]);

  // Filter components
  useEffect(() => {
    let filtered = bomData.components;

    if (searchTerm) {
      filtered = filtered.filter(comp => 
        comp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        comp.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (typeFilter !== 'all') {
      filtered = filtered.filter(comp => comp.type === typeFilter);
    }

    setFilteredComponents(filtered);
  }, [bomData.components, searchTerm, typeFilter]);

  // Filter vulnerabilities
  useEffect(() => {
    if (!bomData.vulnerabilities) return;

    let filtered = bomData.vulnerabilities;

    if (severityFilter !== 'all') {
      filtered = filtered.filter(vuln => 
        vuln.ratings?.[0]?.severity === severityFilter.toUpperCase()
      );
    }

    setFilteredVulnerabilities(filtered);
  }, [bomData.vulnerabilities, severityFilter]);

  const getComponentIcon = (type: string) => {
    switch (type) {
      case 'library': return <Package className="w-4 h-4" />;
      case 'model': return <Database className="w-4 h-4" />;
      case 'dataset': return <FileText className="w-4 h-4" />;
      case 'application': return <Code className="w-4 h-4" />;
      default: return <Package className="w-4 h-4" />;
    }
  };

  const exportBOM = (format: 'json' | 'xml' | 'spdx') => {
    const dataStr = JSON.stringify(bomData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `aibom-${organizationId}-${new Date().toISOString().split('T')[0]}.${format}`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">AI/ML Bill of Materials</h1>
          <p className="text-muted-foreground">
            CycloneDX format - {bomData.metadata.component.name} v{bomData.metadata.component.version}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => exportBOM('json')}>
            <Download className="w-4 h-4 mr-2" />
            Export JSON
          </Button>
          <Button variant="outline" onClick={() => exportBOM('xml')}>
            <Download className="w-4 h-4 mr-2" />
            Export XML
          </Button>
        </div>
      </div>

      {/* Risk Assessment Alert */}
      {riskAssessment.criticalVulns > 0 && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            <strong>Critical Risk Detected:</strong> {riskAssessment.criticalVulns} critical vulnerabilities found. 
            Immediate action required.
          </AlertDescription>
        </Alert>
      )}

      {/* Risk Score */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Risk Assessment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{riskAssessment.totalComponents}</div>
              <div className="text-sm text-muted-foreground">Total Components</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{riskAssessment.totalVulnerabilities}</div>
              <div className="text-sm text-muted-foreground">Vulnerabilities</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{riskAssessment.criticalVulns}</div>
              <div className="text-sm text-muted-foreground">Critical</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{riskAssessment.highVulns}</div>
              <div className="text-sm text-muted-foreground">High</div>
            </div>
          </div>
          <div className="mt-4">
            <div className="flex justify-between text-sm mb-2">
              <span>Risk Score</span>
              <span>{riskAssessment.riskScore.toFixed(1)}%</span>
            </div>
            <Progress value={riskAssessment.riskScore} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="components">Components</TabsTrigger>
          <TabsTrigger value="vulnerabilities">Vulnerabilities</TabsTrigger>
          <TabsTrigger value="dependencies">Dependencies</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Component Type Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Component Types</CardTitle>
                <CardDescription>Distribution of components by type</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={componentTypeData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {componentTypeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Vulnerability Severity Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Vulnerability Severity</CardTitle>
                <CardDescription>Distribution of vulnerabilities by severity</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={vulnerabilitySeverityData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Framework Distribution */}
            {frameworkData.length > 0 && (
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>ML Framework Distribution</CardTitle>
                  <CardDescription>Distribution of ML models by framework</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <Treemap
                      data={frameworkData}
                      dataKey="value"
                      aspectRatio={4 / 3}
                      stroke="#fff"
                      fill="#8884d8"
                    >
                      <Tooltip />
                    </Treemap>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="components" className="space-y-4">
          {/* Component Filters */}
          <Card>
            <CardHeader>
              <CardTitle>Components</CardTitle>
              <CardDescription>All components in the AI/ML project</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 mb-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <input
                      type="text"
                      placeholder="Search components..."
                      className="pl-10 pr-4 py-2 w-full border rounded-md"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                </div>
                <select
                  className="px-3 py-2 border rounded-md"
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                >
                  <option value="all">All Types</option>
                  <option value="library">Library</option>
                  <option value="model">Model</option>
                  <option value="dataset">Dataset</option>
                  <option value="application">Application</option>
                  <option value="framework">Framework</option>
                </select>
              </div>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Version</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Vulnerabilities</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredComponents.map((component) => (
                    <TableRow key={component.bomRef}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getComponentIcon(component.type)}
                          <Badge variant="outline">{component.type}</Badge>
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">{component.name}</TableCell>
                      <TableCell>{component.version}</TableCell>
                      <TableCell className="max-w-xs truncate">
                        {component.description}
                      </TableCell>
                      <TableCell>
                        {component.vulnerabilities ? (
                          <Badge variant="destructive">
                            {component.vulnerabilities.length}
                          </Badge>
                        ) : (
                          <Badge variant="secondary">0</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm">
                          <Eye className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="vulnerabilities" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Vulnerabilities</CardTitle>
              <CardDescription>Security vulnerabilities found in components</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4">
                <select
                  className="px-3 py-2 border rounded-md"
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                >
                  <option value="all">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Component</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredVulnerabilities.map((vuln) => (
                    <TableRow key={vuln.id}>
                      <TableCell className="font-mono text-sm">{vuln.id}</TableCell>
                      <TableCell>
                        <Badge 
                          variant={
                            vuln.ratings?.[0]?.severity === 'CRITICAL' ? 'destructive' :
                            vuln.ratings?.[0]?.severity === 'HIGH' ? 'default' :
                            'secondary'
                          }
                        >
                          {vuln.ratings?.[0]?.severity || 'UNKNOWN'}
                        </Badge>
                      </TableCell>
                      <TableCell>{vuln.affects?.[0]?.ref || 'Unknown'}</TableCell>
                      <TableCell className="max-w-xs truncate">
                        {vuln.description}
                      </TableCell>
                      <TableCell>
                        <a 
                          href={vuln.source.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline"
                        >
                          {vuln.source.name}
                        </a>
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm">
                          <Eye className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="dependencies" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Dependencies</CardTitle>
              <CardDescription>Component dependency relationships</CardDescription>
            </CardHeader>
            <CardContent>
              {bomData.dependencies ? (
                <div className="space-y-4">
                  {bomData.dependencies.map((dep, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <h4 className="font-medium mb-2">{dep.ref}</h4>
                      <div className="space-y-1">
                        {dep.dependsOn.map((dependency, depIndex) => (
                          <div key={depIndex} className="text-sm text-muted-foreground">
                            → {dependency}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No dependency information available</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
