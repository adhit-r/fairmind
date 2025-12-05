'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { IconAlertTriangle, IconCheck } from '@tabler/icons-react';
import { complianceAutomationService, ComplianceViolation } from '@/lib/api/compliance-automation-service';

export default function ViolationAlerts() {
    const [violations, setViolations] = useState<ComplianceViolation[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchViolations();
    }, []);

    const fetchViolations = async () => {
        setLoading(true);
        try {
            const res = await complianceAutomationService.listViolations();
            if (res.success && res.data) {
                setViolations(res.data);
            }
        } catch (error) {
            console.error("Failed to fetch violations", error);
        } finally {
            setLoading(false);
        }
    };

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'critical': return 'bg-red-100 text-red-800 border-red-200';
            case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
            case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
            default: return 'bg-blue-100 text-blue-800 border-blue-200';
        }
    };

    return (
        <Card className="border-2 border-black shadow-brutal h-full">
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-600">
                    <IconAlertTriangle />
                    Active Violations
                    {violations.length > 0 && (
                        <Badge variant="destructive" className="ml-2">{violations.length}</Badge>
                    )}
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 max-h-[400px] overflow-y-auto">
                {violations.length === 0 && !loading ? (
                    <div className="text-center py-8 text-muted-foreground">
                        No active violations. System is compliant.
                    </div>
                ) : (
                    violations.map(violation => (
                        <div key={violation.id} className={`p-3 rounded-lg border ${getSeverityColor(violation.severity)}`}>
                            <div className="flex justify-between items-start">
                                <div>
                                    <div className="font-bold flex items-center gap-2">
                                        {violation.violation_type}
                                        <Badge variant="outline" className="bg-white/50 text-xs uppercase">{violation.severity}</Badge>
                                    </div>
                                    <div className="text-sm mt-1">{violation.description}</div>
                                    <div className="text-xs mt-2 opacity-70">
                                        Framework: {violation.framework} • Detected: {new Date(violation.detected_at).toLocaleDateString()}
                                    </div>
                                </div>
                                <Button size="sm" variant="neutral" className="h-8 w-8 p-0 hover:bg-white/50">
                                    <IconCheck size={16} />
                                </Button>
                            </div>
                        </div>
                    ))
                )}
            </CardContent>
        </Card>
    );
}
