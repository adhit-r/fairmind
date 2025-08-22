"use client"

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/common/card';
import { Button } from '@/components/ui/common/button';
import { Database } from 'lucide-react';

export default function ModelRegistryPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="text-center">
        <Database className="w-16 h-16 mx-auto mb-4 text-gray-400" />
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Model Registry</h1>
        <p className="text-gray-600 mb-6">This page is under development.</p>
        <Button onClick={() => window.history.back()}>
          Go Back
        </Button>
      </div>
    </div>
  );
}
