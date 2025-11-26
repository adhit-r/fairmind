'use client';

import { useState, useEffect } from 'react';
import {
    IconShieldCheck,
    IconAlertTriangle,
    IconFileText,
    IconDownload,
    IconRefresh,
    IconChecklist,
    IconScale,
    IconBook,
    IconRobot,
    IconDatabase,
    IconChartBar,
    IconLock,
    IconBrain,
} from '@tabler/icons-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface Framework {
    id: string;
    name: string;
    description: string;
    region: string;
    status: string;
}

interface ComplianceResult {
    model_id?: string;
    framework: string;
    compliance_score: number;
    overall_status: string;
    total_requirements: number;
    compliant_requirements: number;
    evidence_collected?: number;
    automated_evidence_sources?: string[];
    results: Array<{
        requirement_id: string;
        category: string;
        requirement: string;
        status: string;
        gaps: string[];
        evidence_source?: string;
        evidence_hash?: string;
    }>;
    gaps?: Array<{
        control_id: string;
        control_name: string;
        category: string;
        failed_checks: string[];
    }>;
    note?: string;
}

// Evidence source mapping for visual display
const EVIDENCE_SOURCE_MAP: Record<string, { icon: any; label: string; color: string }> = {
    'fairmind_dataset_service': {
        icon: IconDatabase,
        label: 'Dataset Service',
        color: 'bg-blue-100 text-blue-800'
    },
    'fairmind_bias_detection': {
        icon: IconBrain,
        label: 'Bias Detection',
        color: 'bg-purple-100 text-purple-800'
    },
    'fairmind_model_registry': {
        icon: IconFileText,
        label: 'Model Registry',
        color: 'bg-green-100 text-green-800'
    },
    'fairmind_monitoring_service': {
        icon: IconChartBar,
        label: 'Monitoring',
        color: 'bg-orange-100 text-orange-800'
    },
    'fairmind_security_testing': {
        icon: IconLock,
        label: 'Security Tests',
        color: 'bg-red-100 text-red-800'
    },
    'default': {
        icon: IconFileText,
        label: 'Manual',
        color: 'bg-gray-100 text-gray-800'
    }
};

export default function ComplianceDashboardPage() {
    const [frameworks, setFrameworks] = useState<Framework[]>([]);
    const [selectedFramework, setSelectedFramework] = useState<string>('');
    const [selectedModel, setSelectedModel] = useState<string>('model-demo-001');
    const [complianceResults, setComplianceResults] = useState<ComplianceResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [useAutomated, setUseAutomated] = useState(true);

    useEffect(() => {
        fetchFrameworks();
    }, []);

    const fetchFrameworks = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/v1/compliance/frameworks');
            const data = await response.json();
            setFrameworks(data.frameworks || []);
            if (data.frameworks && data.frameworks.length > 0) {
                setSelectedFramework(data.frameworks[0].id);
            }
        } catch (error) {
            console.error('Error fetching frameworks:', error);
        }
    };

    const checkCompliance = async () => {
        if (!selectedFramework) return;

        setLoading(true);
        try {
            if (useAutomated && selectedModel) {
                // AUTOMATED: Evidence collected automatically from FairMind features
                const response = await fetch(
                    `http://localhost:8000/api/v1/compliance/model/${selectedModel}/compliance?framework=${selectedFramework}`
                );
                const data = await response.json();
                setComplianceResults(data);
            } else {
                // MANUAL: Use sample system data
                const systemData = {
                    name: 'Sample AI System',
                    description: 'AI-powered recommendation system',
                    risk_level: 'high',
                    evidence_EU_AI_1: [{ quality: 0.9, description: 'Risk classification completed' }],
                    evidence_EU_AI_2: [{ quality: 0.85, description: 'Transparency measures implemented' }],
                    evidence_EU_AI_3: [{ quality: 0.8, description: 'Human oversight in place' }],
                    evidence_EU_AI_4: [{ quality: 0.9, description: 'Data governance established' }],
                    evidence_EU_AI_5: [{ quality: 0.95, description: 'Technical documentation maintained' }],
                    evidence_EU_AI_6: [{ quality: 0.88, description: 'Logging system active' }],
                    evidence_EU_AI_7: [{ quality: 0.82, description: 'Accuracy monitoring in place' }],
                    evidence_GDPR_1: [{ quality: 0.9, description: 'Legal basis established' }],
                    evidence_GDPR_2: [{ quality: 0.85, description: 'Data minimization applied' }],
                    evidence_GDPR_3: [{ quality: 0.8, description: 'Automated decision safeguards' }],
                    evidence_GDPR_4: [{ quality: 0.9, description: 'DPIA conducted' }],
                    evidence_ISO_1: [{ quality: 0.85, description: 'AI management system established' }],
                    evidence_ISO_2: [{ quality: 0.88, description: 'Risk management implemented' }],
                    evidence_NIST_1: [{ quality: 0.9, description: 'Governance structure in place' }],
                    evidence_NIST_2: [{ quality: 0.85, description: 'Risk mapping completed' }],
                    evidence_NIST_3: [{ quality: 0.87, description: 'Performance measurement active' }],
                    evidence_IEEE_1: [{ quality: 0.83, description: 'Value-based design applied' }],
                };

                const response = await fetch('http://localhost:8000/api/v1/compliance/check', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        framework: selectedFramework,
                        system_data: systemData,
                    }),
                });

                const data = await response.json();
                setComplianceResults(data);
            }
        } catch (error) {
            console.error('Error checking compliance:', error);
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'compliant':
                return 'bg-green-100 text-green-800 hover:bg-green-100';
            case 'partially_compliant':
                return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100';
            case 'non_compliant':
                return 'bg-red-100 text-red-800 hover:bg-red-100';
            default:
                return 'bg-gray-100 text-gray-800 hover:bg-gray-100';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'compliant':
                return <IconShieldCheck className="h-5 w-5 text-green-600" />;
            case 'partially_compliant':
                return <IconAlertTriangle className="h-5 w-5 text-yellow-600" />;
            case 'non_compliant':
                return <IconAlertTriangle className="h-5 w-5 text-red-600" />;
            default:
                return <IconFileText className="h-5 w-5 text-gray-600" />;
        }
    };

    return (
        <div className="container mx-auto py-8 space-y-8">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Compliance Dashboard</h1>
                    <p className="text-muted-foreground mt-1">
                        Regulatory compliance checks and audit reporting
                    </p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={fetchFrameworks}>
                        <IconRefresh className="mr-2 h-4 w-4" />
                        Refresh
                    </Button>
                    <Button disabled={!complianceResults}>
                        <IconDownload className="mr-2 h-4 w-4" />
                        Export Report
                    </Button>
                </div>
            </div>

            {/* Framework Selection */}
            <Card>
                <CardHeader>
                    <CardTitle>Compliance Check Configuration</CardTitle>
                    <CardDescription>Choose framework and evidence collection method</CardDescription>
                </CardHeader>
                <CardContent>
                    {/* Automated Evidence Toggle */}
                    <Alert className="mb-4 bg-blue-50 border-blue-200">
                        <IconRobot className="h-4 w-4 text-blue-600" />
                        <AlertDescription className="ml-2">
                            <div className="flex items-center justify-between">
                                <span className="font-medium text-blue-900">
                                    {useAutomated ? '✅ Automated Evidence Collection Enabled' : '⚠️ Manual Evidence Mode'}
                                </span>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setUseAutomated(!useAutomated)}
                                    className="ml-4"
                                >
                                    {useAutomated ? 'Switch to Manual' : 'Enable Automated'}
                                </Button>
                            </div>
                            <p className="text-sm text-blue-700 mt-2">
                                {useAutomated
                                    ? 'Evidence will be automatically collected from FairMind\'s bias detection, model registry, monitoring, and security testing features.'
                                    : 'Using sample data for demonstration. Enable automated mode to collect real evidence from your models.'}
                            </p>
                        </AlertDescription>
                    </Alert>

                    <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
                        {useAutomated && (
                            <div className="md:col-span-4">
                                <label className="text-sm font-medium mb-2 block">Model</label>
                                <Select value={selectedModel} onValueChange={setSelectedModel}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select a model" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="model-demo-001">Demo Model 001</SelectItem>
                                        <SelectItem value="model-demo-002">Demo Model 002</SelectItem>
                                        <SelectItem value="model-prod-001">Production Model 001</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        )}
                        <div className={useAutomated ? "md:col-span-4" : "md:col-span-8"}>
                            <label className="text-sm font-medium mb-2 block">Framework</label>
                            <Select value={selectedFramework} onValueChange={setSelectedFramework}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select a regulatory framework" />
                                </SelectTrigger>
                                <SelectContent>
                                    {frameworks.map((f) => (
                                        <SelectItem key={f.id} value={f.id}>
                                            {f.name} - {f.description}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="md:col-span-4">
                            <Button
                                className="w-full"
                                onClick={checkCompliance}
                                disabled={loading || !selectedFramework || (useAutomated && !selectedModel)}
                            >
                                {loading ? 'Checking...' : useAutomated ? 'Check Compliance (Auto)' : 'Check Compliance (Manual)'}
                                {!loading && <IconChecklist className="ml-2 h-4 w-4" />}
                            </Button>
                        </div>
                    </div>

                    {/* Evidence Source Legend */}
                    {useAutomated && (
                        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                            <h4 className="text-sm font-semibold mb-2">Automated Evidence Sources:</h4>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                                {Object.entries(EVIDENCE_SOURCE_MAP).filter(([key]) => key !== 'default').map(([key, { icon: Icon, label, color }]) => (
                                    <div key={key} className="flex items-center gap-2">
                                        <Icon className="h-4 w-4" />
                                        <Badge variant="outline" className={color}>
                                            {label}
                                        </Badge>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Results */}
            {complianceResults && (
                <div className="space-y-6">
                    {/* Overview Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex justify-between items-start mb-4">
                                    <p className="text-sm font-medium text-muted-foreground">Overall Score</p>
                                    {getStatusIcon(complianceResults.overall_status)}
                                </div>
                                <div className="flex items-baseline gap-2">
                                    <span className="text-3xl font-bold">
                                        {complianceResults.compliance_score.toFixed(0)}%
                                    </span>
                                </div>
                                <Progress
                                    value={complianceResults.compliance_score}
                                    className="mt-4"
                                // Note: Shadcn Progress doesn't support color prop directly, usually handled via class or CSS variables
                                />
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex flex-col gap-1">
                                    <p className="text-sm font-medium text-muted-foreground">Status</p>
                                    <Badge className={`w-fit mt-2 ${getStatusColor(complianceResults.overall_status)}`}>
                                        {complianceResults.overall_status.replace('_', ' ').toUpperCase()}
                                    </Badge>
                                    <p className="text-xs text-muted-foreground mt-4">
                                        Framework: {complianceResults.framework}
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex flex-col gap-1">
                                    <p className="text-sm font-medium text-muted-foreground">Requirements Met</p>
                                    <span className="text-3xl font-bold mt-2">
                                        {complianceResults.compliant_requirements} / {complianceResults.total_requirements}
                                    </span>
                                    <Progress
                                        value={(complianceResults.compliant_requirements / complianceResults.total_requirements) * 100}
                                        className="mt-4"
                                    />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex flex-col gap-1">
                                    <p className="text-sm font-medium text-muted-foreground">Total Requirements</p>
                                    <span className="text-3xl font-bold mt-2">
                                        {complianceResults.total_requirements}
                                    </span>
                                    <p className="text-xs text-muted-foreground mt-4">
                                        Assessed requirements
                                    </p>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Automated Evidence Sources Card */}
                    {complianceResults.automated_evidence_sources && complianceResults.automated_evidence_sources.length > 0 && (
                        <Card className="border-2 border-blue-200 bg-blue-50/50">
                            <CardHeader>
                                <div className="flex items-center gap-2">
                                    <IconRobot className="h-5 w-5 text-blue-600" />
                                    <CardTitle className="text-blue-900">Automated Evidence Collection</CardTitle>
                                </div>
                                <CardDescription>
                                    Evidence automatically collected from {complianceResults.evidence_collected} checks across {complianceResults.automated_evidence_sources.length} FairMind features
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                    {complianceResults.automated_evidence_sources.map((source) => {
                                        const sourceInfo = EVIDENCE_SOURCE_MAP[source] || EVIDENCE_SOURCE_MAP['default'];
                                        const Icon = sourceInfo.icon;
                                        return (
                                            <div key={source} className="flex flex-col items-center gap-2 p-4 bg-white rounded-lg border">
                                                <Icon className="h-8 w-8 text-gray-700" />
                                                <Badge className={sourceInfo.color}>
                                                    {sourceInfo.label}
                                                </Badge>
                                                <span className="text-xs text-gray-500 text-center">
                                                    {source.replace('fairmind_', '').replace(/_/g, ' ')}
                                                </span>
                                            </div>
                                        );
                                    })}
                                </div>
                                {complianceResults.note && (
                                    <p className="text-sm text-blue-700 mt-4 p-3 bg-blue-100 rounded">
                                        ℹ️ {complianceResults.note}
                                    </p>
                                )}
                            </CardContent>
                        </Card>
                    )}

                    {/* Detailed Results */}
                    <Card>
                        <CardContent className="p-6">
                            <Tabs defaultValue="overview">
                                <TabsList className="mb-4">
                                    <TabsTrigger value="overview">
                                        <IconScale className="mr-2 h-4 w-4" />
                                        Overview
                                    </TabsTrigger>
                                    <TabsTrigger value="requirements">
                                        <IconChecklist className="mr-2 h-4 w-4" />
                                        Requirements
                                    </TabsTrigger>
                                    <TabsTrigger value="recommendations">
                                        <IconBook className="mr-2 h-4 w-4" />
                                        Recommendations
                                    </TabsTrigger>
                                </TabsList>

                                <TabsContent value="overview" className="space-y-4">
                                    <div>
                                        <h3 className="text-lg font-semibold mb-2">Compliance Overview</h3>
                                        <p className="text-muted-foreground mb-4">
                                            Your system has been assessed against the {complianceResults.framework} framework.
                                            The overall compliance score is {complianceResults.compliance_score.toFixed(1)}%.
                                        </p>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {complianceResults.results.map((result, index) => (
                                            <Card key={index} className="border shadow-sm">
                                                <CardContent className="p-4">
                                                    <div className="flex justify-between items-start mb-2">
                                                        <span className="font-semibold text-sm">{result.category}</span>
                                                        <Badge className={getStatusColor(result.status)}>
                                                            {result.status.replace('_', ' ')}
                                                        </Badge>
                                                    </div>
                                                    <p className="text-xs text-muted-foreground">
                                                        {result.requirement}
                                                    </p>
                                                </CardContent>
                                            </Card>
                                        ))}
                                    </div>
                                </TabsContent>

                                <TabsContent value="requirements">
                                    <div className="rounded-md border">
                                        <Table>
                                            <TableHeader>
                                                <TableRow>
                                                    <TableHead>ID</TableHead>
                                                    <TableHead>Category</TableHead>
                                                    <TableHead>Requirement</TableHead>
                                                    <TableHead>Status</TableHead>
                                                    <TableHead>Gaps</TableHead>
                                                </TableRow>
                                            </TableHeader>
                                            <TableBody>
                                                {complianceResults.results.map((result, index) => (
                                                    <TableRow key={index}>
                                                        <TableCell className="font-medium">{result.requirement_id}</TableCell>
                                                        <TableCell>{result.category}</TableCell>
                                                        <TableCell>{result.requirement}</TableCell>
                                                        <TableCell>
                                                            <Badge className={getStatusColor(result.status)}>
                                                                {result.status.replace('_', ' ')}
                                                            </Badge>
                                                        </TableCell>
                                                        <TableCell>
                                                            {result.gaps.length > 0 ? (
                                                                <Badge variant="destructive">
                                                                    {result.gaps.length} gap(s)
                                                                </Badge>
                                                            ) : (
                                                                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                                                                    No gaps
                                                                </Badge>
                                                            )}
                                                        </TableCell>
                                                    </TableRow>
                                                ))}
                                            </TableBody>
                                        </Table>
                                    </div>
                                </TabsContent>

                                <TabsContent value="recommendations" className="space-y-4">
                                    <div>
                                        <h3 className="text-lg font-semibold mb-4">Recommendations</h3>
                                        <div className="space-y-4">
                                            {complianceResults.results
                                                .filter((r) => r.status !== 'compliant')
                                                .map((result, index) => (
                                                    <Card key={index} className="border-l-4 border-l-orange-500">
                                                        <CardContent className="p-4">
                                                            <div className="flex justify-between items-start mb-2">
                                                                <span className="font-semibold">{result.category}</span>
                                                                <Badge variant="secondary" className="bg-orange-100 text-orange-800">
                                                                    Action Required
                                                                </Badge>
                                                            </div>
                                                            <p className="text-sm mb-2">{result.requirement}</p>
                                                            <div className="space-y-1">
                                                                {result.gaps.map((gap, gapIndex) => (
                                                                    <p key={gapIndex} className="text-xs text-muted-foreground flex items-center">
                                                                        <span className="mr-2">•</span> {gap}
                                                                    </p>
                                                                ))}
                                                            </div>
                                                        </CardContent>
                                                    </Card>
                                                ))}
                                            {complianceResults.results.filter((r) => r.status !== 'compliant').length === 0 && (
                                                <Card className="bg-muted/50">
                                                    <CardContent className="p-8 text-center text-muted-foreground">
                                                        No recommendations - all requirements are met!
                                                    </CardContent>
                                                </Card>
                                            )}
                                        </div>
                                    </div>
                                </TabsContent>
                            </Tabs>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
