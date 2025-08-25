"use client"

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/common/card';
import { Button } from '@/components/ui/common/button';
import { Badge } from '@/components/ui/common/badge';
import { 
  Download, 
  FileText, 
  Code,
  Settings,
  CheckCircle
} from 'lucide-react';

export const AIBOMExport: React.FC = () => {
  const [selectedFormat, setSelectedFormat] = useState('cyclonedx');
  const [isExporting, setIsExporting] = useState(false);

  const exportFormats = [
    { id: 'cyclonedx', name: 'CycloneDX', description: 'Industry standard SBOM format', icon: Code },
    { id: 'spdx', name: 'SPDX', description: 'Software Package Data Exchange format', icon: FileText },
    { id: 'json', name: 'JSON', description: 'Custom JSON format', icon: Settings }
  ];

  const handleExport = async () => {
    setIsExporting(true);
    // Simulate export
    setTimeout(() => {
      setIsExporting(false);
      // In a real app, this would trigger a download
      console.log(`Exporting in ${selectedFormat} format`);
    }, 2000);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="w-5 h-5" />
            Export AI BOM
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-3">
                Export Format
              </label>
              <div className="grid gap-3">
                {exportFormats.map((format) => (
                  <div
                    key={format.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedFormat === format.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedFormat(format.id)}
                  >
                    <div className="flex items-center gap-3">
                      <format.icon className="w-5 h-5 text-gray-600" />
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">
                          {format.name}
                        </div>
                        <div className="text-sm text-gray-600">
                          {format.description}
                        </div>
                      </div>
                      {selectedFormat === format.id && (
                        <CheckCircle className="w-5 h-5 text-blue-600" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <Button 
              onClick={handleExport}
              disabled={isExporting}
              className="w-full"
            >
              {isExporting ? (
                <>
                  <Download className="w-4 h-4 mr-2 animate-spin" />
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Export BOM
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Export Options
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Include component details</span>
              <Badge variant="secondary">Enabled</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Include vulnerability data</span>
              <Badge variant="secondary">Enabled</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Include license information</span>
              <Badge variant="secondary">Enabled</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Include compliance data</span>
              <Badge variant="secondary">Enabled</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
