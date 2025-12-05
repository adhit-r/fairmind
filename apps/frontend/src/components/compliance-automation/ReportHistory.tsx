'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { IconFileText, IconDownload } from '@tabler/icons-react';

export default function ReportHistory() {
    // Mock data for now
    const reports = [
        { id: '1', name: 'EU AI Act Compliance Report', date: '2023-11-28', status: 'Generated' },
        { id: '2', name: 'Weekly Bias Audit', date: '2023-11-21', status: 'Generated' },
        { id: '3', name: 'GDPR Data Privacy Check', date: '2023-11-15', status: 'Generated' },
    ];

    return (
        <Card className="border-2 border-black shadow-brutal h-full">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <IconFileText />
                    Recent Reports
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
                {reports.map(report => (
                    <div key={report.id} className="flex items-center justify-between p-3 border-b last:border-0 hover:bg-gray-50 rounded">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-gray-100 rounded text-gray-600">
                                <IconFileText size={18} />
                            </div>
                            <div>
                                <div className="font-medium text-sm">{report.name}</div>
                                <div className="text-xs text-muted-foreground">{report.date}</div>
                            </div>
                        </div>
                        <Button variant="neutral" size="icon">
                            <IconDownload size={16} />
                        </Button>
                    </div>
                ))}
                <Button variant="noShadow" className="w-full text-xs text-muted-foreground mt-2">
                    View All Reports
                </Button>
            </CardContent>
        </Card>
    );
}
