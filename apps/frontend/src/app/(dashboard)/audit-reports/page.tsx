'use client';

import { useState } from 'react';
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    CardDescription,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from '@/components/ui/accordion';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';
import {
    IconFileText,
    IconDownload,
    IconCheck,
    IconClock,
    IconScale,
    IconBook,
    IconFileAnalytics,
} from '@tabler/icons-react';
import { cn } from '@/lib/utils';

interface AuditReport {
    report_id: string;
    system_id: string;
    report_date: string;
    system_name: string;
    system_description: string;
    risk_level: string;
    overall_compliance_score: number;
    frameworks_assessed: string[];
    compliance_results: Array<{
        framework: string;
        compliance_score: number;
        overall_status: string;
        total_requirements: number;
        compliant_requirements: number;
    }>;
    executive_summary: string;
    recommendations: Array<{
        framework: string;
        recommendation: string;
        priority: string;
    }>;
    next_review_date: string;
}

export default function AuditReportsPage() {
    const [systemId, setSystemId] = useState('');
    const [systemName, setSystemName] = useState('');
    const [systemDescription, setSystemDescription] = useState('');
    const [riskLevel, setRiskLevel] = useState<string>('');
    const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>([]);
    const [auditReport, setAuditReport] = useState<AuditReport | null>(null);
    const [loading, setLoading] = useState(false);

    const frameworks = [
        { value: 'EU AI Act', label: 'EU AI Act' },
        { value: 'GDPR', label: 'GDPR' },
        { value: 'ISO 42001', label: 'ISO 42001' },
        { value: 'NIST AI RMF', label: 'NIST AI RMF' },
        { value: 'IEEE 7000', label: 'IEEE 7000' },
        { value: 'DPDP Act', label: 'DPDP Act (India)' },
        { value: 'India AI', label: 'India AI' },
    ];

    const riskLevels = [
        { value: 'minimal', label: 'Minimal Risk' },
        { value: 'limited', label: 'Limited Risk' },
        { value: 'high', label: 'High Risk' },
        { value: 'unacceptable', label: 'Unacceptable Risk' },
    ];

    const generateAuditReport = async () => {
        if (!systemId || !systemName) {
            alert('Please fill in system ID and name');
            return;
        }

        setLoading(true);
        try {
            // Sample system data with evidence
            const systemData = {
                name: systemName,
                description: systemDescription,
                risk_level: riskLevel,
                evidence_EU_AI_1: [{ quality: 0.9, description: 'Risk classification completed' }],
                evidence_EU_AI_2: [{ quality: 0.85, description: 'Transparency measures implemented' }],
                evidence_EU_AI_3: [{ quality: 0.8, description: 'Human oversight in place' }],
                evidence_EU_AI_4: [{ quality: 0.9, description: 'Data governance established' }],
                evidence_EU_AI_5: [{ quality: 0.95, description: 'Technical documentation maintained' }],
                evidence_EU_AI_6: [{ quality: 0.88, description: 'Logging system active' }],
                evidence_EU_AI_7: [{ quality: 0.82, description: 'Accuracy monitoring in place' }],
                evidence_EU_AI_8: [{ quality: 0.78, description: 'Cybersecurity measures in place' }],
                evidence_GDPR_1: [{ quality: 0.9, description: 'Legal basis established' }],
                evidence_GDPR_2: [{ quality: 0.85, description: 'Data minimization applied' }],
                evidence_GDPR_3: [{ quality: 0.8, description: 'Automated decision safeguards' }],
                evidence_GDPR_4: [{ quality: 0.9, description: 'DPIA conducted' }],
                evidence_GDPR_5: [{ quality: 0.87, description: 'Explanation mechanisms in place' }],
                evidence_ISO_1: [{ quality: 0.85, description: 'AI management system established' }],
                evidence_ISO_2: [{ quality: 0.88, description: 'Risk management implemented' }],
                evidence_ISO_3: [{ quality: 0.83, description: 'Personnel competence ensured' }],
                evidence_NIST_1: [{ quality: 0.9, description: 'Governance structure in place' }],
                evidence_NIST_2: [{ quality: 0.85, description: 'Risk mapping completed' }],
                evidence_NIST_3: [{ quality: 0.87, description: 'Performance measurement active' }],
                evidence_NIST_4: [{ quality: 0.84, description: 'Risk management strategies implemented' }],
                evidence_IEEE_1: [{ quality: 0.83, description: 'Value-based design applied' }],
            };

            const response = await fetch('http://localhost:8000/api/v1/compliance/audit-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    system_id: systemId,
                    system_data: systemData,
                    frameworks: selectedFrameworks.length > 0 ? selectedFrameworks : null,
                }),
            });

            const data = await response.json();
            setAuditReport(data);
        } catch (error) {
            console.error('Error generating audit report:', error);
            alert('Error generating audit report');
        } finally {
            setLoading(false);
        }
    };

    const downloadReport = () => {
        if (!auditReport) return;

        const reportText = `
AUDIT REPORT
============

Report ID: ${auditReport.report_id}
System: ${auditReport.system_name}
Date: ${new Date(auditReport.report_date).toLocaleDateString()}

EXECUTIVE SUMMARY
${auditReport.executive_summary}

COMPLIANCE RESULTS
Overall Score: ${auditReport.overall_compliance_score.toFixed(1)}%
Risk Level: ${auditReport.risk_level}

Frameworks Assessed:
${auditReport.frameworks_assessed.map((f) => `- ${f}`).join('\n')}

DETAILED RESULTS
${auditReport.compliance_results
                .map(
                    (r) => `
${r.framework}
Score: ${r.compliance_score.toFixed(1)}%
Status: ${r.overall_status}
Requirements Met: ${r.compliant_requirements}/${r.total_requirements}
`
                )
                .join('\n')}

RECOMMENDATIONS
${auditReport.recommendations
                .map((r) => `[${r.priority.toUpperCase()}] ${r.framework}: ${r.recommendation}`)
                .join('\n')}

Next Review Date: ${new Date(auditReport.next_review_date).toLocaleDateString()}
    `;

        const blob = new Blob([reportText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit-report-${auditReport.report_id}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
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

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'high':
                return 'destructive';
            case 'medium':
                return 'default'; // Using default for medium/yellow-ish if available or just default
            case 'low':
                return 'secondary';
            default:
                return 'outline';
        }
    };

    return (
        <div className="container mx-auto py-8 max-w-7xl space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Audit Reports</h1>
                <p className="text-muted-foreground mt-2">
                    Generate comprehensive compliance audit reports
                </p>
            </div>

            {/* Report Generation Form */}
            <Card>
                <CardHeader>
                    <CardTitle>Generate New Audit Report</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                System ID
                            </label>
                            <Input
                                placeholder="e.g., SYS-001"
                                value={systemId}
                                onChange={(e) => setSystemId(e.currentTarget.value)}
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                System Name
                            </label>
                            <Input
                                placeholder="e.g., Recommendation Engine"
                                value={systemName}
                                onChange={(e) => setSystemName(e.currentTarget.value)}
                                required
                            />
                        </div>
                        <div className="col-span-full space-y-2">
                            <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                System Description
                            </label>
                            <Textarea
                                placeholder="Describe the AI system..."
                                value={systemDescription}
                                onChange={(e) => setSystemDescription(e.currentTarget.value)}
                                className="min-h-[80px]"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                Risk Level
                            </label>
                            <Select value={riskLevel} onValueChange={setRiskLevel}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select risk level" />
                                </SelectTrigger>
                                <SelectContent>
                                    {riskLevels.map((level) => (
                                        <SelectItem key={level.value} value={level.value}>
                                            {level.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                Frameworks to Assess
                            </label>
                            <Select
                                value={selectedFrameworks[0] || ''}
                                onValueChange={(value) => setSelectedFrameworks(value ? [value] : [])}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select framework (optional)" />
                                </SelectTrigger>
                                <SelectContent>
                                    {frameworks.map((fw) => (
                                        <SelectItem key={fw.value} value={fw.value}>
                                            {fw.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <Button
                        onClick={generateAuditReport}
                        disabled={loading}
                        className="w-full md:w-auto"
                        size="lg"
                    >
                        {loading ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                            <IconFileAnalytics className="mr-2 h-4 w-4" />
                        )}
                        Generate Audit Report
                    </Button>
                </CardContent>
            </Card>

            {/* Loading State */}
            {loading && (
                <Card>
                    <CardContent className="flex flex-col items-center justify-center py-10 space-y-4">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <p className="text-muted-foreground">Generating comprehensive audit report...</p>
                    </CardContent>
                </Card>
            )}

            {/* Audit Report */}
            {auditReport && !loading && (
                <div className="space-y-6">
                    {/* Report Header */}
                    <Card>
                        <CardContent className="p-6">
                            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                                <div>
                                    <p className="text-xs text-muted-foreground uppercase font-semibold tracking-wider">
                                        Report ID
                                    </p>
                                    <p className="font-mono font-bold text-lg">{auditReport.report_id}</p>
                                </div>
                                <Button variant="outline" onClick={downloadReport}>
                                    <IconDownload className="mr-2 h-4 w-4" />
                                    Download Report
                                </Button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                                <div>
                                    <p className="text-xs text-muted-foreground uppercase font-semibold tracking-wider">
                                        System Name
                                    </p>
                                    <p className="font-semibold mt-1">{auditReport.system_name}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-muted-foreground uppercase font-semibold tracking-wider">
                                        Report Date
                                    </p>
                                    <p className="font-semibold mt-1">
                                        {new Date(auditReport.report_date).toLocaleDateString()}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-xs text-muted-foreground uppercase font-semibold tracking-wider">
                                        Risk Level
                                    </p>
                                    <Badge
                                        variant={auditReport.risk_level === 'high' ? 'destructive' : 'secondary'}
                                        className="mt-1"
                                    >
                                        {auditReport.risk_level}
                                    </Badge>
                                </div>
                                <div>
                                    <p className="text-xs text-muted-foreground uppercase font-semibold tracking-wider">
                                        Overall Score
                                    </p>
                                    <p className="text-2xl font-bold text-green-600 mt-1">
                                        {auditReport.overall_compliance_score.toFixed(1)}%
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Executive Summary */}
                    <Card>
                        <CardHeader className="flex flex-row items-center gap-4 space-y-0">
                            <div className="p-2 bg-primary/10 rounded-full">
                                <IconFileText className="h-6 w-6 text-primary" />
                            </div>
                            <CardTitle>Executive Summary</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="whitespace-pre-line leading-relaxed text-muted-foreground">
                                {auditReport.executive_summary}
                            </p>
                        </CardContent>
                    </Card>

                    {/* Compliance Results */}
                    <Card>
                        <CardHeader className="flex flex-row items-center gap-4 space-y-0">
                            <div className="p-2 bg-blue-100 rounded-full">
                                <IconScale className="h-6 w-6 text-blue-600" />
                            </div>
                            <CardTitle>Compliance Results</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {auditReport.compliance_results.map((result, index) => (
                                    <div
                                        key={index}
                                        className="p-4 border rounded-lg bg-card text-card-foreground shadow-sm"
                                    >
                                        <div className="flex justify-between items-start mb-2">
                                            <h3 className="font-semibold">{result.framework}</h3>
                                            <Badge className={getStatusColor(result.overall_status)} variant="outline">
                                                {result.overall_status.replace('_', ' ')}
                                            </Badge>
                                        </div>
                                        <div className="mt-4">
                                            <p className="text-3xl font-bold">
                                                {result.compliance_score.toFixed(1)}%
                                            </p>
                                            <p className="text-sm text-muted-foreground mt-1">
                                                {result.compliant_requirements} / {result.total_requirements}{' '}
                                                requirements met
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Recommendations */}
                    <Card>
                        <CardHeader className="flex flex-row items-center gap-4 space-y-0">
                            <div className="p-2 bg-orange-100 rounded-full">
                                <IconBook className="h-6 w-6 text-orange-600" />
                            </div>
                            <CardTitle>Recommendations</CardTitle>
                        </CardHeader>
                        <CardContent>
                            {auditReport.recommendations.length > 0 ? (
                                <Accordion type="single" collapsible className="w-full">
                                    {auditReport.recommendations.map((rec, index) => (
                                        <AccordionItem key={index} value={`rec-${index}`}>
                                            <AccordionTrigger className="hover:no-underline">
                                                <div className="flex items-center gap-3 text-left">
                                                    <Badge variant={getPriorityColor(rec.priority) as any}>
                                                        {rec.priority.toUpperCase()}
                                                    </Badge>
                                                    <span className="text-sm font-medium">{rec.framework}</span>
                                                </div>
                                            </AccordionTrigger>
                                            <AccordionContent>
                                                <p className="text-muted-foreground">{rec.recommendation}</p>
                                            </AccordionContent>
                                        </AccordionItem>
                                    ))}
                                </Accordion>
                            ) : (
                                <Alert className="bg-green-50 border-green-200">
                                    <IconCheck className="h-4 w-4 text-green-600" />
                                    <AlertTitle className="text-green-800">Excellent!</AlertTitle>
                                    <AlertDescription className="text-green-700">
                                        No recommendations - all requirements are met!
                                    </AlertDescription>
                                </Alert>
                            )}
                        </CardContent>
                    </Card>

                    {/* Next Review */}
                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center gap-4">
                                <div className="p-2 bg-violet-100 rounded-full">
                                    <IconClock className="h-6 w-6 text-violet-600" />
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground font-medium">
                                        Next Review Date
                                    </p>
                                    <p className="text-lg font-bold mt-1">
                                        {new Date(auditReport.next_review_date).toLocaleDateString()}
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
