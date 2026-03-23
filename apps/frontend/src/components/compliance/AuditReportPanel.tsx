'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertCircle, Download, Loader } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface AuditReportPanelProps {
  onGenerateReport: (format: 'json' | 'csv' | 'pdf', startDate: string, endDate: string) => Promise<void>;
  isLoading: boolean;
  error?: string;
  success?: boolean;
}

export function AuditReportPanel({
  onGenerateReport,
  isLoading,
  error,
  success
}: AuditReportPanelProps) {
  const [format, setFormat] = useState<'json' | 'csv' | 'pdf'>('csv');
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 30);
    return date.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => {
    return new Date().toISOString().split('T')[0];
  });

  const handleGenerate = async () => {
    await onGenerateReport(format, startDate, endDate);
  };

  return (
    <Card className="border-4 border-black shadow-brutal">
      <CardHeader className="border-b-4 border-black">
        <CardTitle className="text-xl font-bold tracking-tight">AUDIT REPORT GENERATOR</CardTitle>
        <CardDescription>Generate compliance audit reports for your organization</CardDescription>
      </CardHeader>
      <CardContent className="pt-6">
        {error && (
          <Alert className="mb-6 border-2 border-red-600 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800 font-medium">{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="mb-6 border-2 border-green-600 bg-green-50">
            <AlertDescription className="text-green-800 font-medium">
              ✓ Report generated! Downloading...
            </AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
          {/* Start Date */}
          <div className="md:col-span-3">
            <label className="block text-sm font-bold mb-2">START DATE</label>
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="border-2 border-black focus:ring-2 focus:ring-orange-500"
            />
          </div>

          {/* End Date */}
          <div className="md:col-span-3">
            <label className="block text-sm font-bold mb-2">END DATE</label>
            <Input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="border-2 border-black focus:ring-2 focus:ring-orange-500"
            />
          </div>

          {/* Format */}
          <div className="md:col-span-2">
            <label className="block text-sm font-bold mb-2">FORMAT</label>
            <Select value={format} onValueChange={(value: any) => setFormat(value)}>
              <SelectTrigger className="border-2 border-black">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="csv">CSV</SelectItem>
                <SelectItem value="json">JSON</SelectItem>
                <SelectItem value="pdf">PDF</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Generate Button */}
          <div className="md:col-span-4 flex items-end">
            <Button
              onClick={handleGenerate}
              disabled={isLoading}
              className="w-full bg-orange-600 text-white font-bold border-2 border-black shadow-brutal hover:shadow-brutal-lg transition-all disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader className="mr-2 h-4 w-4 animate-spin" />
                  GENERATING...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  GENERATE REPORT
                </>
              )}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
