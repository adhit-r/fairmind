"use client"

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/common/card';
import { Button } from '@/components/ui/common/button';
import { Badge } from '@/components/ui/common/badge';
import { 
  Shield, 
  CheckCircle, 
  AlertTriangle,
  XCircle,
  Clock,
  FileText
} from 'lucide-react';

export const AIBOMCompliance: React.FC = () => {
  const [complianceResults, setComplianceResults] = useState<any>({
    gdpr: { status: 'compliant', score: 85 },
    ccpa: { status: 'compliant', score: 92 },
    sox: { status: 'warning', score: 78 },
    hipaa: { status: 'non-compliant', score: 45 }
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'compliant':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
      case 'non-compliant':
        return <XCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compliant':
        return 'bg-green-100 text-green-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'non-compliant':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Compliance Assessment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(complianceResults).map(([regulation, data]: [string, any]) => (
              <div key={regulation} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  {getStatusIcon(data.status)}
                  <div>
                    <div className="font-medium text-gray-900">
                      {regulation.toUpperCase()}
                    </div>
                    <div className="text-sm text-gray-600">
                      Compliance Score: {data.score}%
                    </div>
                  </div>
                </div>
                <Badge className={getStatusColor(data.status)}>
                  {data.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Compliance Report
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-medium text-green-900 mb-2">Compliant Regulations</h4>
                <ul className="text-sm text-green-700 space-y-1">
                  <li>• GDPR - 85% compliant</li>
                  <li>• CCPA - 92% compliant</li>
                </ul>
              </div>
              <div className="p-4 bg-yellow-50 rounded-lg">
                <h4 className="font-medium text-yellow-900 mb-2">Needs Attention</h4>
                <ul className="text-sm text-yellow-700 space-y-1">
                  <li>• SOX - 78% compliant</li>
                </ul>
              </div>
            </div>
            <div className="p-4 bg-red-50 rounded-lg">
              <h4 className="font-medium text-red-900 mb-2">Critical Issues</h4>
              <ul className="text-sm text-red-700 space-y-1">
                <li>• HIPAA - 45% compliant (requires immediate action)</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
